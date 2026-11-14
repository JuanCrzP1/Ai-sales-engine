"""Cómo se reconoce el medio de pago que escribe la IA, con cualquier medio que tenga el negocio.

La IA nombra el medio como aparece en los medios del negocio («Nequi», «transferencia a Davivienda», «Nu», «link de pago»), en su
acción (`metadata.send_payment`) o en su mensaje. Aquí se convierte ese nombre en la clave del negocio: cada medio por su nombre en el
catálogo (`payment_catalog.py`), cada banco por su nombre y cada «otro medio» por el nombre que le puso el negocio.

Solo reconoce nombres. Qué quiere el cliente (pagar, pedir los datos, preguntar) lo entiende la IA, no este archivo.
"""
from __future__ import annotations

import re

from app.domain.business_config.payment_accounts import accounts, options
from app.domain.business_config.payment_catalog import method_kind

# Cómo se nombra el enlace de pago.
_LINK = r"\blink\b|\benlace\b|\bpago en l[ií]nea\b|\bpse\b|\btarjeta de cr[eé]dito\b"


def _word(name: str) -> str:
    return rf"\b{re.escape(name.lower())}\b"


def named_option(text: str, runtime_yaml: dict) -> str:
    """El único medio o cuenta del negocio que nombra el texto, o "": `nequi`, `bank:davivienda` (si nombra el banco), `bank` (si
    habla de transferencia bancaria sin decir cuál), `custom:nu`…"""
    lowered = str(text or "").lower()
    offered = options(runtime_yaml)
    found: list[str] = []
    banks = {account.key: account.own_name for account in accounts(runtime_yaml) if account.option == "bank" and account.own_name}
    named_banks = [key for key, bank in banks.items() if re.search(_word(bank), lowered)]
    for option in offered:
        if option == "link":
            hit = bool(re.search(_LINK, lowered))
        elif option == "bank":
            if len(named_banks) == 1:
                found.append(named_banks[0])
                continue
            kind = method_kind("bank")
            hit = bool(named_banks) or bool(kind and re.search(kind.aliases, lowered))
        elif option.startswith("custom:"):
            name = next((account.own_name for account in accounts(runtime_yaml) if account.option == option), "")
            hit = bool(name) and bool(re.search(_word(name), lowered))
        else:
            kind = method_kind(option)
            hit = bool(kind and re.search(kind.aliases, lowered))
        if hit:
            found.append(option)
    return found[0] if len(found) == 1 else ""


def resolve(value: str, runtime_yaml: dict) -> str:
    """Lo que la IA puso como medio («nequi», «Nequi», «transferencia a Bancolombia», «Nu»), como clave del negocio, o ""."""
    text = str(value or "").strip().lower()
    if not text:
        return ""
    offered = options(runtime_yaml)
    keys = {account.key for account in accounts(runtime_yaml)}
    if text in offered or text in keys:
        return text
    return named_option(text, runtime_yaml)


def refine(key: str, *texts: str, runtime_yaml: dict) -> str:
    """Si se sabe el medio pero no la cuenta («bank») y la IA nombra uno de los bancos del negocio, esa cuenta."""
    if key != "bank":
        return key
    for text in texts:
        named = named_option(text, runtime_yaml)
        if named.startswith("bank:"):
            return named
    return key


# Las palabras con las que se habla de pagarle a alguien, además del nombre del medio.
_PAYING = r"\bcuenta\b|\bconsign\w*|\btransf\w*|\bpag\w*|\bdeposit\w*|\bgir\w*"


def payment_terms(runtime_yaml: dict) -> str:
    """Una expresión que reconoce cuándo se nombra un medio de pago del negocio (o se habla de pagar): «Nequi», «transferencia a
    Davivienda», «Nu», «la cuenta», «págale». La usa el cuidado de números de pago (`payment_data.mask_invented_numbers`)."""
    terms = [_PAYING]
    for option in options(runtime_yaml):
        kind = method_kind(option.split(":", 1)[0])
        if kind is not None and kind.aliases and not kind.custom:
            terms.append(kind.aliases)
    terms += [_word(account.own_name) for account in accounts(runtime_yaml) if account.own_name]
    return "|".join(f"(?:{term})" for term in terms)
