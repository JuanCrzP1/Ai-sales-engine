"""Los datos de pago: la IA decide, el sistema los envía. Con cualquier medio que tenga el negocio, de cualquier país.

La IA nunca ve los números, cuentas, llaves ni enlaces de pago (se equivocaría en un dígito, o se los daría a quien no debe). Para
que salgan, la IA usa una acción: `metadata.send_payment` con el medio («Nequi», «Yape», «transferencia a Davivienda»). El sistema arma
el mensaje con los datos reales y la plantilla del negocio. Las piezas:

- `domain/business_config/payment_accounts.py`: las cuentas del negocio y el mensaje con sus datos.
- `payment_requests.py`: qué medio nombra o pide el cliente (o la IA).
- Aquí, la decisión (`deliver`), en este orden:
  1. **La acción** de la IA, con un medio que el negocio tiene.
  2. **El medio elegido** (`payment_method` con intención de compra): sus datos salen si todavía no se enviaron. Si ya salieron y el
     cliente sigue hablando del mismo pago, responde la IA: los datos no se repiten encima de su respuesta.
  3. **El cliente los pidió o eligió el medio con todas las letras** («envíame el Nequi», «¿y si te pago por Nu?»): salen, diga lo
     que diga la IA (un modelo pequeño a veces responde «no puedo enviarlo», o que «los datos son los mismos»).
  4. **La red de seguridad**: si la IA nombró los datos (su marcador) sin decir el medio, el sistema lo deduce o pregunta con cuál.
     Nunca envía una frase cortada ni el marcador.

Cada vez que actúa una red (3 o 4) queda registrado (`pago_red_de_seguridad`), para ver si la IA falla antes de que un cliente se queje.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.application.pipeline.payment_requests import asked_for_payment_details, asks_for_person, chose_payment_method, named_option, refine, resolve
from app.domain.business_config.payment_accounts import option_of, options, payment_message, same_payment, which_method_question
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE
from app.domain.operations.operational_state import OperationalState
from app.utils.logger import logger

# El paso de la conversación después de enviar los datos: el cliente paga y envía el comprobante.
AWAITING_PAYMENT = "report_payment"
PAYMENT_STATE_HOURS = 6


@dataclass(frozen=True)
class PaymentDelivery:
    """Lo que se le responde al cliente y, si salieron datos de pago, de qué medio o cuenta. `rescue` dice qué red actuó."""

    text: str
    method: str = ""
    rescue: str = ""


def _template(runtime_yaml: dict) -> str | None:
    """La plantilla del negocio para los datos de pago (Mensajes → «Cómo le llegan los datos de pago»), o None: la de la plataforma."""
    config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    return str(config.get("payment_details_message") or "").strip() or None


def ejecutar_pago(runtime_yaml: dict, payment_method: str) -> str:
    """El mensaje con los datos reales de ese medio o cuenta (con la plantilla del negocio), o "" si no lo tiene activo."""
    return payment_message(runtime_yaml, resolve(payment_method, runtime_yaml), _template(runtime_yaml))


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


def _send(runtime_yaml: dict, key: str, rescue: str = "", tenant: str = "") -> PaymentDelivery:
    if rescue:
        logger.warning("pago_red_de_seguridad", extra={"tenant": tenant, "how": rescue, "method": key})
    return PaymentDelivery(payment_message(runtime_yaml, key, _template(runtime_yaml)), key, rescue)


def deliver(
    response_text: str,
    runtime_yaml: dict,
    *,
    send_payment: str = "",
    payment_method: str = "",
    intent: str = "",
    user_message: str = "",
    state: OperationalState | None = None,
    remembered: str = "",
    tenant: str = "",
) -> PaymentDelivery:
    """Qué recibe el cliente: la respuesta de la IA o el mensaje con los datos de pago (ver el orden arriba). `remembered` es el medio
    que el cliente ya había elegido en la conversación: sirve aunque después hablaran de otra cosa (por ejemplo, de activar el
    servicio) y el paso de pago ya no esté activo."""
    offered = options(runtime_yaml)
    if not offered:
        return PaymentDelivery(response_text)
    texts = (user_message, response_text)
    # La IA dice el medio («bank», «Nequi»); si el cliente nombró uno de los bancos del negocio, va esa cuenta.
    action = refine(resolve(send_payment, runtime_yaml), *texts, runtime_yaml=runtime_yaml)
    chosen = refine(resolve(payment_method, runtime_yaml), *texts, runtime_yaml=runtime_yaml)
    if action:
        return _send(runtime_yaml, action)
    if chosen and intent == "buy" and not already_sent(state, chosen):
        return _send(runtime_yaml, chosen)
    in_payment = state.active_option if state and state.is_active() and state.active_process == "payment" else ""
    current = in_payment or resolve(remembered, runtime_yaml)
    asked = asked_for_payment_details(user_message, runtime_yaml, current=current)
    if asked:
        return _send(runtime_yaml, asked, "cliente_pidio_los_datos", tenant)
    # El cliente eligió otro medio («¿y si te pago por Nu?»): salen sus datos, aunque la IA no lo haya marcado.
    switched = chose_payment_method(user_message, runtime_yaml)
    if switched and not already_sent(state, switched):
        return _send(runtime_yaml, switched, "cliente_eligio_el_medio", tenant)
    if REDACTED_PAYMENT_VALUE not in response_text:
        return PaymentDelivery(response_text)

    # La IA nombró los datos sin decir el medio: el sistema lo deduce, o pregunta con cuál.
    candidates = (
        ("medio_elegido", chosen),
        ("mensaje_del_cliente", named_option(user_message, runtime_yaml)),
        ("respuesta_de_la_ia", named_option(response_text, runtime_yaml)),
        ("medio_en_curso", current if option_of(current) in offered else ""),
        ("unico_medio", offered[0] if len(offered) == 1 else ""),
    )
    how, method = next(((how, method) for how, method in candidates if method), ("pregunta", ""))
    if method:
        return _send(runtime_yaml, method, how, tenant)
    logger.warning("pago_red_de_seguridad", extra={"tenant": tenant, "how": how, "method": ""})
    return PaymentDelivery(which_method_question(runtime_yaml), "", how)


def without_payment_placeholder(response_text: str, runtime_yaml: dict, payment_method: str) -> str:
    """El marcador nunca le llega al cliente: con el medio, los datos reales; sin él, el medio que se deduzca o la pregunta."""
    if REDACTED_PAYMENT_VALUE not in response_text:
        return response_text
    return deliver(response_text, runtime_yaml, payment_method=payment_method).text


def keeps_handoff(delivery: PaymentDelivery, user_message: str) -> bool:
    """Si el sistema envió los datos que el cliente pidió, el chat no pasa a una persona por eso (la IA a veces lo pasa porque cree
    que no puede enviarlos), salvo que el cliente también lo haya pedido."""
    return delivery.rescue not in ("cliente_pidio_los_datos", "cliente_eligio_el_medio") or asks_for_person(user_message)
