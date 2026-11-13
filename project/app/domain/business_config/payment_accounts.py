"""Las cuentas de pago de un negocio, listas para enviar, y el mensaje con sus datos reales. Puro: trabaja sobre lo publicado.

Cada cuenta tiene su clave: `link`, el tipo del catálogo (`nequi`, `yape`…), `bank:<banco>` para cada banco y `custom:<nombre>`
para «otro medio». Un medio que se ofrece (`option`) agrupa cuentas: `bank` son todos los bancos del negocio y `nequi`, todas sus
cuentas Nequi. Pedir un medio envía todas sus cuentas en un solo mensaje; pedir una cuenta (`bank:davivienda`), solo esa.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.domain.business_config.payment_catalog import PAYMENT_METHODS, method_kind
from app.domain.business_config.payment_data import iter_payment_blocks
from app.domain.business_config.payment_message import DEFAULT_CASH_DETAILS, LINK_NAME, method_parts, render_payment_details

# Cómo se nombra cada medio en una frase («¿Con qué medio prefieres pagar: pago en línea, Nequi o …?»).
_COMMON_WORDS = ("Transferencia", "Depósito", "Efectivo", "Cuenta")
_PLURAL_NAMES = {"bank": "Transferencia bancaria"}


@dataclass(frozen=True)
class Account:
    """Una cuenta activa y completa: su tipo, su clave, el medio que la ofrece y sus datos reales como salen en el mensaje."""

    kind: str
    key: str
    option: str
    medio: str
    datos: str
    titular: str = ""
    instrucciones: str = ""
    # El nombre por el que el cliente la pide, además del tipo: el banco o el nombre de «otro medio».
    own_name: str = ""


def slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", str(text or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def option_of(key: str) -> str:
    """El medio que ofrece esa cuenta: `bank:davivienda` → `bank`; las demás claves son su propio medio."""
    return "bank" if str(key or "").startswith("bank:") else str(key or "")


def _account(item: dict) -> Account | None:
    kind = str(item.get("type") or "").strip().lower()
    catalog = method_kind(kind)
    if catalog is None:
        return None
    medio, datos = method_parts(kind, item)
    if not datos:
        return None
    titular = str(item.get("holder") or "").strip()
    # En el efectivo, la instrucción ya es el dato: no se repite.
    instrucciones = "" if catalog.data is None else str(item.get("instructions") or "").strip()
    if catalog.needs_bank:
        bank = str(item.get("bank") or "").strip()
        return Account(kind, f"bank:{slug(bank)}", "bank", medio, datos, titular, instrucciones, bank)
    if catalog.custom:
        name = str(item.get("name") or "").strip()
        key = f"custom:{slug(name)}"
        return Account(kind, key, key, medio, datos, titular, instrucciones, name)
    return Account(kind, kind, kind, medio, datos, titular, instrucciones)


def accounts(runtime_yaml: dict) -> list[Account]:
    """Todas las cuentas activas y completas del negocio, sin repetir: primero su enlace de pago (uno solo) y luego las demás."""
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    link: list[Account] = []
    others: list[Account] = []
    seen: set[tuple[str, str]] = set()
    for payment in iter_payment_blocks(pricing):
        url = str(payment.get("link") or "").strip()
        if url and not link:
            link.append(Account("link", "link", "link", LINK_NAME, url))
        transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
        if not bool(transfer.get("enabled", False)):
            continue
        for item in transfer.get("methods") if isinstance(transfer.get("methods"), list) else []:
            account = _account(item) if isinstance(item, dict) else None
            if account is not None and (account.key, account.datos) not in seen:
                seen.add((account.key, account.datos))
                others.append(account)
    return link + others


def options(runtime_yaml: dict) -> list[str]:
    """Los medios que se le pueden ofrecer al cliente, en el orden del catálogo (el enlace primero y «otros medios» al final)."""
    found = {account.option for account in accounts(runtime_yaml)}
    order = ["link", *(kind.id for kind in PAYMENT_METHODS if not kind.custom)]
    customs = [account.option for account in accounts(runtime_yaml) if account.option.startswith("custom:")]
    return [option for option in order if option in found] + list(dict.fromkeys(customs))


def payment_message(runtime_yaml: dict, key: str, template: str | None = None) -> str:
    """El mensaje con los datos reales de un medio (todas sus cuentas) o de una cuenta, o "" si el negocio no lo tiene activo."""
    wanted = str(key or "").strip().lower()
    chosen = [account for account in accounts(runtime_yaml) if wanted and wanted in (account.key, account.option)]
    if not chosen:
        return ""
    if len(chosen) == 1:
        account = chosen[0]
        # El efectivo no tiene comprobante: si el negocio no escribió su plantilla, la de la plataforma para el efectivo.
        chosen_template = template or (DEFAULT_CASH_DETAILS if account.kind == "cash" else None)
        return render_payment_details(chosen_template, medio=account.medio, datos=account.datos, titular=account.titular, instrucciones=account.instrucciones)
    # Varias cuentas del mismo medio: cada una con su nombre, sus datos, su titular y su instrucción, en un solo mensaje.
    blocks = [
        "\n".join(filter(None, (f"*{account.medio}*", account.datos, f"A nombre de: {account.titular}" if account.titular else "", account.instrucciones)))
        for account in chosen
    ]
    medio = _PLURAL_NAMES.get(chosen[0].kind, chosen[0].medio)
    return render_payment_details(template, medio=medio, datos="\n\n".join(blocks))


def option_label(runtime_yaml: dict, option: str) -> str:
    """Cómo se nombra un medio en una frase: «Nequi», «pago en línea», «transferencia a Bancolombia o Davivienda», «Nu»."""
    if option == "link":
        return LINK_NAME[0].lower() + LINK_NAME[1:]
    if option == "bank":
        banks = list(dict.fromkeys(account.own_name for account in accounts(runtime_yaml) if account.option == "bank" and account.own_name))
        return f"transferencia a {' o '.join(banks)}" if banks else "transferencia bancaria"
    if option.startswith("custom:"):
        return next((account.own_name for account in accounts(runtime_yaml) if account.option == option), option)
    kind = method_kind(option)
    if kind is None:
        return option
    return kind.name[0].lower() + kind.name[1:] if kind.name.startswith(_COMMON_WORDS) else kind.name


def which_method_question(runtime_yaml: dict) -> str:
    """La pregunta cuando no se sabe con qué medio quiere pagar el cliente, con los nombres de los medios del negocio."""
    labels = [option_label(runtime_yaml, option) for option in options(runtime_yaml)]
    if len(labels) > 1:
        return f"¿Con qué medio prefieres pagar: {', '.join(labels[:-1])} o {labels[-1]}?"
    return f"¿Te envío los datos para pagar por {labels[0]}?" if labels else "¿Con qué medio prefieres pagar?"


def same_payment(first: str, second: str) -> bool:
    """Si dos claves son el mismo pago: iguales, o el mismo medio cuando una no dice cuál cuenta (`bank` y `bank:davivienda`)."""
    if not first or not second:
        return False
    return first == second or ((first == option_of(first) or second == option_of(second)) and option_of(first) == option_of(second))
