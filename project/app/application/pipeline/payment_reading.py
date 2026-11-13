"""El lector de pagos: qué pide el cliente sobre el pago en este mensaje, entendido por la IA en una llamada corta.

Este sistema es AI-first: aquí no hay reglas de palabras. Antes de que responda el asesor, una llamada corta y enfocada al modelo del
negocio (con su clave) dice dos cosas del mensaje del cliente:

- si **debe recibir los datos para pagar** (y de qué medio): porque los pide, porque dice con qué medio paga o porque acepta que se
  los envíen. Entonces le llegan, pase lo que pase con la respuesta del asesor. Preguntar «¿puedo transferir?» no es pedirlos;
- si **dice que ya pagó**: entonces el chat pasa al equipo, que es quien verifica un pago.

Se le pregunta poco a propósito: con una pregunta más («¿elige el medio?») acertaba menos (medido con la IA real).

El asesor recibe lo que entendió el lector (`sections/conversation.py`) y escribe su mensaje sabiéndolo. Si el lector no responde (sin
clave, un error del proveedor, una respuesta que no se entiende), no hay lectura: decide el asesor solo, como en cualquier otro
mensaje. El texto del lector está en `infrastructure/ai/prompting/payment_reader.py`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from app.application.pipeline.payment_delivery import already_sent, current_method, sent_label
from app.application.pipeline.payment_names import refine, resolve
from app.domain.business_config.payment_accounts import option_of, options
from app.domain.operations.operational_state import OperationalState
from app.infrastructure.ai.prompting.payment_reader import reader_prompt, reader_turn
from app.utils.logger import logger


@dataclass(frozen=True)
class PaymentReading:
    """Lo que entendió el lector del mensaje del cliente. `method` es la clave del negocio (`nequi`, `bank:davivienda`) del medio
    cuyos datos debe recibir: el que nombró o, si no nombró ninguno, el que venían usando; "" si no se sabe."""

    wants_details: bool = False
    method: str = ""
    says_paid: bool = False

    def for_prompt(self, runtime_yaml: dict) -> dict:
        """Lo que se le cuenta al asesor de este mensaje (`runtime["payment_reading"]`)."""
        return {
            "wants_details": self.wants_details,
            # Con varios medios, los datos solo salen cuando el cliente debe recibirlos: el asesor lo sabe antes de responder.
            "no_details_now": not self.wants_details and len(options(runtime_yaml)) > 1,
            "method": sent_label(runtime_yaml, self.method) if self.method else "",
            "says_paid": self.says_paid,
        }


def _json(raw: str) -> dict | None:
    text = str(raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def read_customer_message(
    runtime,
    *,
    bot_config,
    runtime_yaml: dict,
    user_message: str,
    state: OperationalState | None = None,
    remembered: str = "",
    tenant: str = "",
) -> PaymentReading | None:
    """Lo que pide el cliente sobre el pago en este mensaje, o None si no hay lectura (el negocio no tiene medios de pago, el motor no
    tiene lector o la llamada falló)."""
    offered = options(runtime_yaml)
    classify = getattr(runtime, "classify", None)
    if not offered or not callable(classify) or not str(user_message or "").strip():
        return None
    current = current_method(state, remembered, runtime_yaml)
    sent = sent_label(runtime_yaml, current) if current and already_sent(state, current) else ""
    try:
        raw = classify(reader_prompt(runtime_yaml), user_message=reader_turn(runtime_yaml, user_message, sent=sent), bot_config=bot_config)
    except Exception as error:  # noqa: BLE001 - sin lector, decide el asesor solo
        logger.warning("pago_lectura_fallida", extra={"tenant": tenant, "error": type(error).__name__})
        return None
    answer = _json(raw)
    if answer is None or "recibe_datos_de_pago" not in answer:
        logger.warning("pago_lectura_fallida", extra={"tenant": tenant, "error": "formato"})
        return None
    wants = answer.get("recibe_datos_de_pago") is True
    method = ""
    if wants:
        # El medio que nombró el cliente; si no nombró ninguno, el que venían usando; si el negocio tiene uno solo, ese.
        said = str(answer.get("medio") or "")
        named = refine(resolve(said, runtime_yaml), said, runtime_yaml=runtime_yaml)
        method = named or (current if option_of(current) in offered else "") or (offered[0] if len(offered) == 1 else "")
    reading = PaymentReading(wants_details=wants, method=method, says_paid=answer.get("dice_que_ya_pago") is True)
    logger.info("pago_lectura", extra={"tenant": tenant, "wants_details": reading.wants_details, "method": reading.method, "says_paid": reading.says_paid})
    return reading
