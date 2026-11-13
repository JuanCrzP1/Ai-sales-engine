"""Los datos de pago: la IA decide, el sistema los envía.

La IA nunca ve los números, cuentas, llaves ni enlaces de pago (se equivocaría en un dígito, o se los daría a quien no debe). Para
que salgan, la IA usa una acción: `metadata.send_payment` con el medio («envíale los datos de Nequi»). Lo hace cuando el cliente
elige cómo pagar y cuando los pide otra vez («se me borró el número»). El sistema arma el mensaje con los datos reales y la plantilla
del negocio (`domain/business_config/payment_message.py`).

Así se decide, en orden (`deliver`):
1. **La acción.** Si la IA pidió enviar los datos de un medio que el negocio tiene, salen.
2. **El medio elegido** (`payment_method` con intención de compra, como antes de la acción): salen si todavía no se enviaron. Si ya
   se enviaron y el cliente sigue hablando del mismo pago, responde la IA: los datos no se repiten encima de su respuesta.
3. **La red de seguridad.** Si la IA nombró los datos (su marcador) sin decir el medio, el sistema lo deduce: del mensaje del cliente,
   de lo que escribió la IA, del medio con el que venían pagando o del único medio que tiene el negocio. Si no hay forma de saberlo,
   le pregunta al cliente con cuál prefiere pagar. Nunca envía una frase cortada ni el marcador. Cada vez que actúa queda registrado
   (`pago_red_de_seguridad`), para ver si la IA está fallando antes de que un cliente se queje.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE
from app.domain.business_config.payment_message import method_parts, render_payment_details
from app.domain.operations.operational_state import OperationalState
from app.utils.logger import logger

# Los medios que la plataforma sabe entregar, en el orden en que se ofrecen.
PAYMENT_METHOD_TYPES = ("link", "nequi", "daviplata", "bank", "breb")
# El paso de la conversación después de enviar los datos: el cliente paga y envía el comprobante.
AWAITING_PAYMENT = "report_payment"
PAYMENT_STATE_HOURS = 6
_SIGNALS = {
    "nequi": r"\bnequi\b",
    "daviplata": r"\bdaviplata\b",
    "breb": r"\bbre-?b\b|\bllave\b",
    "link": r"\blink\b|\benlace\b|\bpago en l[ií]nea\b|\bpse\b|\btarjeta\b",
    "bank": r"\bbanco\b|\bbancaria\b|\bcuenta de ahorros\b|\bcuenta corriente\b|\bbancolombia\b",
}


@dataclass(frozen=True)
class PaymentDelivery:
    """Lo que se le responde al cliente y, si salieron datos de pago, de qué medio. `rescue` dice cómo actuó la red de seguridad."""

    text: str
    method: str = ""
    rescue: str = ""


# ---------------------------------------------------------------------------------------------------------- el mensaje


def _iter_payment_blocks(pricing: dict) -> list[dict]:
    blocks: list[dict] = []
    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []
    for plan in plans:
        if isinstance(plan, dict) and isinstance(plan.get("payment"), dict) and plan["payment"]:
            blocks.append(plan["payment"])
    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    if isinstance(catalog.get("payment"), dict) and catalog["payment"]:
        blocks.append(catalog["payment"])
    if isinstance(pricing.get("payment"), dict) and pricing["payment"]:
        blocks.append(pricing["payment"])
    return blocks


def _payment_details_template(runtime_yaml: dict) -> str | None:
    """La plantilla del negocio para los datos de pago (Mensajes → «Cómo le llegan los datos de pago»), o None: la de la plataforma."""
    config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    return str(config.get("payment_details_message") or "").strip() or None


@dataclass(frozen=True)
class _Account:
    """Una cuenta del negocio lista para enviar: su tipo, su clave propia (`bank:davivienda` si es un banco) y sus datos reales."""

    kind: str
    key: str
    medio: str
    datos: str
    titular: str
    bank: str = ""


def _slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def _accounts(runtime_yaml: dict) -> list[_Account]:
    """Todas las cuentas activas y completas del negocio, en orden, sin repetir: el enlace y cada cuenta de transferencia."""
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    found: list[_Account] = []
    seen: set[tuple[str, str]] = set()
    for payment in _iter_payment_blocks(pricing):
        link = str(payment.get("link") or "").strip()
        if link and ("link", link) not in seen:
            seen.add(("link", link))
            medio, datos = method_parts("link", {"link": link})
            found.append(_Account("link", "link", medio, datos, ""))
        transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
        if not bool(transfer.get("enabled", False)):
            continue
        for item in transfer.get("methods") if isinstance(transfer.get("methods"), list) else []:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("type") or "").strip().lower()
            medio, datos = method_parts(kind, item)
            if not datos or (kind, datos) in seen:
                continue
            seen.add((kind, datos))
            bank = str(item.get("bank") or "").strip() if kind == "bank" else ""
            key = f"bank:{_slug(bank)}" if bank else kind
            found.append(_Account(kind, key, medio, datos, str(item.get("holder") or "").strip(), bank))
    # Solo el primer enlace: un negocio cobra por un solo link.
    links = [account for account in found if account.kind == "link"][:1]
    return links + [account for account in found if account.kind != "link"]


def _kind(key: str) -> str:
    return str(key or "").split(":", 1)[0]


def same_payment(first: str, second: str) -> bool:
    """Si dos medios son el mismo pago: iguales, o del mismo tipo cuando uno no dice cuál cuenta (`bank` y `bank:davivienda`)."""
    if not first or not second:
        return False
    return first == second or ((":" not in first or ":" not in second) and _kind(first) == _kind(second))


_PLURAL = {"bank": "Transferencia bancaria", "nequi": "Nequi", "daviplata": "Daviplata", "breb": "Bre-B"}


def ejecutar_pago(runtime_yaml: dict, payment_method: str) -> str:
    """El mensaje con los datos reales de ese medio, o "" si el negocio no lo tiene activo. `bank` envía todas las cuentas bancarias
    en un solo mensaje; `bank:davivienda`, solo esa."""
    key = str(payment_method or "").strip().lower()
    if not key:
        return ""
    chosen = [account for account in _accounts(runtime_yaml) if account.key == key or (":" not in key and account.kind == key)]
    if not chosen:
        return ""
    template = _payment_details_template(runtime_yaml)
    if len(chosen) == 1:
        account = chosen[0]
        return render_payment_details(template, medio=account.medio, datos=account.datos, titular=account.titular)
    # Varias cuentas del mismo tipo: cada una con su nombre, sus datos y su titular, en un solo mensaje.
    blocks = [f"*{account.medio}*\n{account.datos}" + (f"\nA nombre de: {account.titular}" if account.titular else "") for account in chosen]
    return render_payment_details(template, medio=_PLURAL.get(chosen[0].kind, chosen[0].medio), datos="\n\n".join(blocks))


def available_methods(runtime_yaml: dict) -> list[str]:
    """Los tipos de pago cuyos datos el sistema puede enviar ahora (activos y completos), en el orden en que se ofrecen."""
    kinds = {account.kind for account in _accounts(runtime_yaml)}
    return [kind for kind in PAYMENT_METHOD_TYPES if kind in kinds]


def _banks(runtime_yaml: dict) -> list[_Account]:
    return [account for account in _accounts(runtime_yaml) if account.kind == "bank"]


def _label(runtime_yaml: dict, method: str) -> str:
    if method == "bank":
        names = [account.bank for account in _banks(runtime_yaml) if account.bank]
        return f"transferencia a {' o '.join(names)}" if names else "transferencia bancaria"
    return {"link": "pago en línea", "nequi": "Nequi", "daviplata": "Daviplata", "breb": "Bre-B"}.get(method, method)


def which_method_question(runtime_yaml: dict) -> str:
    labels = [_label(runtime_yaml, method) for method in available_methods(runtime_yaml)]
    if len(labels) > 1:
        return f"¿Con qué medio prefieres pagar: {', '.join(labels[:-1])} o {labels[-1]}?"
    return f"¿Te envío los datos para pagar por {labels[0]}?" if labels else "¿Con qué medio prefieres pagar?"


# ---------------------------------------------------------------------------------------------------------- la decisión


def _named(text: str, methods: list[str], runtime_yaml: dict) -> str:
    """El único medio del negocio que nombra el texto, o "". Si nombra uno de sus bancos, esa cuenta (`bank:davivienda`)."""
    lowered = str(text or "").lower()
    banks = [account for account in _banks(runtime_yaml) if account.bank]
    named_banks = [account.key for account in banks if re.search(rf"\b{re.escape(account.bank.lower())}\b", lowered)]
    signals = dict(_SIGNALS)
    if named_banks:
        signals["bank"] = r"(?!)"  # ya se sabe cuál banco
    found = [method for method in methods if re.search(signals.get(method, re.escape(method)), lowered)]
    if len(named_banks) == 1 and "bank" in methods:
        found = [key for key in found if key != "bank"] + named_banks
    elif len(named_banks) > 1:
        found = [key for key in found if key != "bank"] + ["bank"]
    return found[0] if len(found) == 1 else ""


def _refine(key: str, *texts: str, runtime_yaml: dict) -> str:
    """Si la IA dijo «bank» y el cliente (o la IA) nombra uno de los bancos del negocio, esa cuenta."""
    if key != "bank":
        return key
    for text in texts:
        named = _named(text, ["bank"], runtime_yaml)
        if named.startswith("bank:"):
            return named
    return key


# Pedir algo: «envíame», «pásame», «dame», «¿cuál es…?», «se me borró», «no me llegó», «otra vez»…
_REQUEST = re.compile(
    r"\b(env[ií]a(me|melo|mela|los)?|m[aá]nda(me|melo|mela)?|p[aá]sa(me|melo|mela)?|da(me|melo|mela)|reenv[ií]a(me|melo)?|"
    r"rep[ií]te(me|melo)?|comp[aá]rte(me|melo)?|cu[aá]l es|me (das|pasas|env[ií]as|mandas|compartes|repites)|necesito|"
    r"me lo (env[ií]as|mandas|pasas|das|repites)|se me borr[oó]|no me lleg[oó]|no lo (tengo|encuentro|veo)|otra vez|de nuevo)\b"
)
# Lo que pide son los datos de pago (sin nombrar el medio): «el número», «la cuenta», «los datos para pagar», «el link de pago».
_PAYMENT_DATA = re.compile(
    r"\b(datos (de|para) pag\w*|n[uú]mero (de|para) (pag\w*|la cuenta|cuenta)|n[uú]mero|la cuenta|cuenta (de|para) pag\w*|"
    r"link (de|para) pag\w*|enlace (de|para) pag\w*|la llave)\b"
)
# Lo que no es un pedido de datos de pago aunque lo parezca: el número o la cuenta de otra cosa.
_NOT_PAYMENT = re.compile(
    r"\b(whatsapp|contacto|direcci[oó]n|horario|p[aá]gina|web|instagram|pedido|gu[ií]a|tienda|local|asesor|vendedor|domicilio|"
    r"informaci[oó]n|info|cat[aá]logo|foto|precio|plan)\b"
)
# «Me lo envías de nuevo», «se me borró»: un pedido corto que solo puede ser lo último que se le envió.
_AGAIN = re.compile(r"\b(otra vez|de nuevo|se me borr[oó]|no me lleg[oó]|me lo (env[ií]as|mandas|pasas|das|repites))\b")
_SHORT_REQUEST_WORDS = 7


def asked_for_payment_details(message: str, methods: list[str], runtime_yaml: dict, *, current: str = "") -> str:
    """El medio cuyos datos pide el cliente con todas las letras («envíame el Nequi», «se me borró el número, ¿me lo envías?»), o "".

    Hace falta un pedido y saber de qué medio: el que nombra, o el que venían usando si pide «el número» o «de nuevo»."""
    text = str(message or "").lower()
    if not methods or not _REQUEST.search(text) or _NOT_PAYMENT.search(text):
        return ""
    named = _named(text, methods, runtime_yaml)
    if named:
        return named
    if _PAYMENT_DATA.search(text) or (_AGAIN.search(text) and len(text.split()) <= _SHORT_REQUEST_WORDS):
        if _kind(current) in methods:
            return current
        return methods[0] if len(methods) == 1 else ""
    return ""


def sent_state(method: str, now: datetime | None = None) -> OperationalState:
    """El paso de la conversación después de enviar los datos de `method`: falta que el cliente pague y envíe el comprobante."""
    moment = now or datetime.now(timezone.utc)
    return OperationalState(active_process="payment", active_option=method, pending_action=AWAITING_PAYMENT, expires_at=moment + timedelta(hours=PAYMENT_STATE_HOURS))


def already_sent(state: OperationalState | None, method: str) -> bool:
    """Si ya se le enviaron al cliente los datos de ese medio (o de esa misma cuenta) y falta que pague."""
    return bool(
        state and state.is_active() and state.active_process == "payment" and state.pending_action == AWAITING_PAYMENT
        and same_payment(state.active_option, method)
    )


def deliver(
    response_text: str,
    runtime_yaml: dict,
    *,
    send_payment: str = "",
    payment_method: str = "",
    intent: str = "",
    user_message: str = "",
    state: OperationalState | None = None,
    tenant: str = "",
) -> PaymentDelivery:
    """Qué recibe el cliente: la respuesta de la IA o el mensaje con los datos de pago (ver el orden arriba)."""
    methods = available_methods(runtime_yaml)
    # La IA dice el tipo («bank»); si el cliente nombró uno de los bancos del negocio, va esa cuenta.
    action = _refine(send_payment, user_message, response_text, runtime_yaml=runtime_yaml) if _kind(send_payment) in methods else ""
    chosen = _refine(payment_method, user_message, response_text, runtime_yaml=runtime_yaml) if _kind(payment_method) in methods else ""
    if action:
        return PaymentDelivery(ejecutar_pago(runtime_yaml, action), action)
    if chosen and intent == "buy" and not already_sent(state, chosen):
        return PaymentDelivery(ejecutar_pago(runtime_yaml, chosen), chosen)
    current = state.active_option if state and state.is_active() and state.active_process == "payment" else ""
    # El cliente pidió los datos con todas las letras: salen, diga lo que diga la IA (un modelo pequeño a veces responde «no puedo
    # enviarlo», sobre todo si ya lo dijo antes en la conversación).
    asked = asked_for_payment_details(user_message, methods, runtime_yaml, current=current)
    if asked:
        logger.warning("pago_red_de_seguridad", extra={"tenant": tenant, "how": "cliente_pidio_los_datos", "method": asked})
        return PaymentDelivery(ejecutar_pago(runtime_yaml, asked), asked, "cliente_pidio_los_datos")
    if REDACTED_PAYMENT_VALUE not in response_text:
        return PaymentDelivery(response_text)

    # La IA nombró los datos sin decir el medio: el sistema lo deduce, o pregunta.
    candidates = (
        ("medio_elegido", chosen),
        ("mensaje_del_cliente", _named(user_message, methods, runtime_yaml)),
        ("respuesta_de_la_ia", _named(response_text, methods, runtime_yaml)),
        ("medio_en_curso", current if _kind(current) in methods else ""),
        ("unico_medio", methods[0] if len(methods) == 1 else ""),
    )
    how, method = next(((how, method) for how, method in candidates if method), ("pregunta", ""))
    logger.warning("pago_red_de_seguridad", extra={"tenant": tenant, "how": how, "method": method})
    if method:
        return PaymentDelivery(ejecutar_pago(runtime_yaml, method), method, how)
    return PaymentDelivery(which_method_question(runtime_yaml), "", how)


def without_payment_placeholder(response_text: str, runtime_yaml: dict, payment_method: str) -> str:
    """El marcador nunca le llega al cliente: con el medio, los datos reales; sin él, el medio que se deduzca o la pregunta."""
    if REDACTED_PAYMENT_VALUE not in response_text:
        return response_text
    return deliver(response_text, runtime_yaml, payment_method=payment_method).text


# Pedir una persona con todas las letras.
_ASKS_FOR_PERSON = re.compile(r"\b(una persona|un humano|alguien (del equipo|real)|un asesor|hablar con|que me (llamen|atienda))\b")


def keeps_handoff(delivery: PaymentDelivery, user_message: str) -> bool:
    """Si el sistema envió los datos que el cliente pidió, el chat no pasa a una persona por eso (la IA a veces lo pasa porque cree
    que no puede enviarlos), salvo que el cliente también lo haya pedido."""
    if delivery.rescue != "cliente_pidio_los_datos":
        return True
    return bool(_ASKS_FOR_PERSON.search(str(user_message or "").lower()))
