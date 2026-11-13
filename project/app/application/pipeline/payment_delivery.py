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


def ejecutar_pago(runtime_yaml: dict, payment_method: str) -> str:
    """El mensaje con los datos reales de ese medio, o "" si el negocio no lo tiene activo."""
    method = str(payment_method or "").strip().lower()
    if not method:
        return ""
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    payment_links: list[str] = []
    transfer_methods: dict[str, dict] = {}
    for payment in _iter_payment_blocks(pricing):
        link = str(payment.get("link") or "").strip()
        if link and link not in payment_links:
            payment_links.append(link)
        transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
        if not bool(transfer.get("enabled", False)):
            continue
        for item in transfer.get("methods") if isinstance(transfer.get("methods"), list) else []:
            if isinstance(item, dict):
                item_type = str(item.get("type") or "").strip().lower()
                if item_type and item_type not in transfer_methods:
                    transfer_methods[item_type] = dict(item)

    template = _payment_details_template(runtime_yaml)
    if method == "link":
        if not payment_links:
            return ""
        medio, datos = method_parts("link", {"link": payment_links[0]})
        return render_payment_details(template, medio=medio, datos=datos)
    selected = transfer_methods.get(method)
    if not selected:
        return ""
    medio, datos = method_parts(method, selected)
    if not datos:
        return ""
    return render_payment_details(template, medio=medio, datos=datos, titular=str(selected.get("holder") or ""))


def available_methods(runtime_yaml: dict) -> list[str]:
    """Los medios cuyos datos el sistema puede enviar ahora (activos y completos)."""
    return [method for method in PAYMENT_METHOD_TYPES if ejecutar_pago(runtime_yaml, method)]


def _label(runtime_yaml: dict, method: str) -> str:
    if method == "bank":
        medio, _datos = method_parts("bank", _first_bank(runtime_yaml))
        return f"transferencia a {medio}" if medio else "transferencia bancaria"
    return {"link": "pago en línea", "nequi": "Nequi", "daviplata": "Daviplata", "breb": "Bre-B"}.get(method, method)


def _first_bank(runtime_yaml: dict) -> dict:
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    for payment in _iter_payment_blocks(pricing):
        transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
        for item in transfer.get("methods") if isinstance(transfer.get("methods"), list) else []:
            if isinstance(item, dict) and str(item.get("type") or "").lower() == "bank":
                return item
    return {}


def which_method_question(runtime_yaml: dict) -> str:
    labels = [_label(runtime_yaml, method) for method in available_methods(runtime_yaml)]
    if len(labels) > 1:
        return f"¿Con qué medio prefieres pagar: {', '.join(labels[:-1])} o {labels[-1]}?"
    return f"¿Te envío los datos para pagar por {labels[0]}?" if labels else "¿Con qué medio prefieres pagar?"


# ---------------------------------------------------------------------------------------------------------- la decisión


def _named(text: str, methods: list[str], runtime_yaml: dict) -> str:
    """El único medio del negocio que nombra el texto, o ""."""
    lowered = str(text or "").lower()
    signals = dict(_SIGNALS)
    bank = str(_first_bank(runtime_yaml).get("bank") or "").strip().lower()
    if bank:
        signals["bank"] = signals["bank"] + rf"|\b{re.escape(bank)}\b"
    found = [method for method in methods if re.search(signals.get(method, re.escape(method)), lowered)]
    return found[0] if len(found) == 1 else ""


def sent_state(method: str, now: datetime | None = None) -> OperationalState:
    """El paso de la conversación después de enviar los datos de `method`: falta que el cliente pague y envíe el comprobante."""
    moment = now or datetime.now(timezone.utc)
    return OperationalState(active_process="payment", active_option=method, pending_action=AWAITING_PAYMENT, expires_at=moment + timedelta(hours=PAYMENT_STATE_HOURS))


def already_sent(state: OperationalState | None, method: str) -> bool:
    return bool(state and state.is_active() and state.active_process == "payment" and state.active_option == method and state.pending_action == AWAITING_PAYMENT)


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
    action = send_payment if send_payment in methods else ""
    chosen = payment_method if payment_method in methods else ""
    if action:
        return PaymentDelivery(ejecutar_pago(runtime_yaml, action), action)
    if chosen and intent == "buy" and not already_sent(state, chosen):
        return PaymentDelivery(ejecutar_pago(runtime_yaml, chosen), chosen)
    if REDACTED_PAYMENT_VALUE not in response_text:
        return PaymentDelivery(response_text)

    # La IA nombró los datos sin decir el medio: el sistema lo deduce, o pregunta.
    current = state.active_option if state and state.is_active() and state.active_process == "payment" else ""
    candidates = (
        ("medio_elegido", chosen),
        ("mensaje_del_cliente", _named(user_message, methods, runtime_yaml)),
        ("respuesta_de_la_ia", _named(response_text, methods, runtime_yaml)),
        ("medio_en_curso", current if current in methods else ""),
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
