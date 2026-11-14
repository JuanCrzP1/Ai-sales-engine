"""El resumen de lo que pasó antes en una conversación larga, escrito por la IA.

La IA ve los últimos mensajes de la conversación (`prompting/history.py`); en un chat largo, lo del principio queda fuera: el nombre
del cliente, su negocio, el plan que quería. Cuando hay suficientes mensajes que la IA ya no ve y que el resumen todavía no cubre
(`SUMMARY_BATCH`), una llamada corta al modelo del negocio (con su clave) escribe el resumen nuevo a partir del anterior y de esos
mensajes. Se guarda en la memoria del cliente con la hora del último mensaje que cubre, y le llega al asesor en cada mensaje
(`sections/conversation.py`).

- Se hace pocas veces: una llamada cada `SUMMARY_BATCH` mensajes, solo en conversaciones largas. Suma al consumo del negocio.
- Nunca lleva datos de pago: los mensajes que lee y el resumen que escribe pasan por `redact_payment_values`.
- Si la llamada falla, queda el resumen anterior y el aviso `resumen_fallido`: el asesor responde igual.
"""
from __future__ import annotations

import json
import logging

from app.domain.business_config.payment_data import redact_payment_values
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.ai.prompting import summary_writer
from app.infrastructure.ai.prompting.history import MAX_MESSAGES

logger = logging.getLogger("assistant")

# Cuántos mensajes que la IA ya no ve hacen falta para escribir un resumen nuevo.
SUMMARY_BATCH = 10
# El largo máximo del resumen: unas cinco frases.
MAX_SUMMARY_CHARS = 700
_ROLES = {"user": "Cliente", "assistant": "Asesor"}


def _json(raw: str) -> dict:
    text = str(raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    try:
        parsed = json.loads(text[start : end + 1]) if start >= 0 and end > start else {}
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def refresh_summary(
    runtime,
    *,
    bot_config,
    memory: MemoryDomainService,
    runtime_yaml: dict,
    tenant_slug: str,
    user_id: str,
) -> str:
    """El resumen de lo que pasó antes en la conversación, al día: el guardado o, si ya toca, uno nuevo. "" si no hay."""
    summary, until = memory.get_summary(tenant_slug=tenant_slug, user_id=user_id)
    entries = memory.get_history_entries(tenant_slug=tenant_slug, user_id=user_id)
    # Los mensajes que la IA ya no ve (los anteriores a los últimos) y que el resumen todavía no cubre.
    unseen = entries[:-MAX_MESSAGES] if len(entries) > MAX_MESSAGES else []
    pending = [entry for entry in unseen if entry.get("at") is not None and (until is None or entry["at"] > until)]
    classify = getattr(runtime, "classify", None)
    if len(pending) < SUMMARY_BATCH or not callable(classify):
        return summary
    lines = [summary_writer.SUMMARY_PREVIOUS.format(summary=summary)] if summary else []
    lines.append(summary_writer.SUMMARY_NEW_MESSAGES)
    lines += [f"{_ROLES.get(entry.get('role'), 'Cliente')}: {entry.get('text')}" for entry in pending]
    try:
        raw = classify(summary_writer.SUMMARY_WRITER, user_message=redact_payment_values("\n".join(lines), runtime_yaml), bot_config=bot_config, max_tokens=300)
    except Exception as error:  # noqa: BLE001 - sin resumen nuevo, el asesor responde con el anterior
        logger.warning("resumen_fallido", extra={"tenant": tenant_slug, "error": type(error).__name__})
        return summary
    written = " ".join(str(_json(raw).get("resumen") or "").split())
    if not written:
        logger.warning("resumen_fallido", extra={"tenant": tenant_slug, "error": "formato"})
        return summary
    written = redact_payment_values(written, runtime_yaml)[:MAX_SUMMARY_CHARS]
    memory.set_summary(tenant_slug=tenant_slug, user_id=user_id, summary=written, until=pending[-1]["at"])
    logger.info("resumen_actualizado", extra={"tenant": tenant_slug, "mensajes": len(pending)})
    return written
