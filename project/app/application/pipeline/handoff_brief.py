"""El resumen para el equipo cuando un chat pasa a una persona, escrito por la IA.

Quien atiende llega al chat sin haberlo leído. El aviso (campana, correo, celular) y el chat del panel le dicen, en dos o tres frases,
quién es el cliente, qué necesita y qué pidió (como los traspasos de Intercom o Zendesk). Antes el aviso solo traía el último mensaje
del cliente: con «No, gracias, prefiero una persona», el equipo no sabía de qué se trataba.

- Una llamada corta al modelo del negocio (con su clave), solo cuando el chat pasa a una persona. Suma poco al consumo del negocio.
- Lee los últimos mensajes y, en un chat largo, el resumen de lo anterior (`conversation_summary.py`).
- Nunca lleva datos de pago: lo que lee y lo que escribe pasan por `redact_payment_values`.
- Si la llamada falla, no hay resumen y el aviso lleva el último mensaje del cliente, como antes; queda el aviso
  `resumen_para_el_equipo_fallido`.
"""
from __future__ import annotations

import json
import logging

from app.domain.business_config.conversations import HANDOFF_REASONS, handoff_reason_text
from app.domain.business_config.payment_data import redact_payment_values
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.ai.prompting import handoff_brief_writer

logger = logging.getLogger("assistant")

# Cuántos mensajes recientes lee: suficientes para entender el pedido sin pagar por todo el chat.
BRIEF_MESSAGES = 12
# El largo máximo de la nota: unas tres frases.
MAX_BRIEF_CHARS = 400
_ROLES = {"user": "Cliente", "assistant": "Asesor"}


def _json(raw: str) -> dict:
    text = str(raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    try:
        parsed = json.loads(text[start : end + 1]) if start >= 0 and end > start else {}
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def brief_for_team(
    runtime,
    *,
    bot_config,
    memory: MemoryDomainService | None,
    runtime_yaml: dict,
    tenant_slug: str,
    user_id: str,
    reason: str,
) -> str:
    """La nota para el equipo sobre este chat, o "" si no se pudo escribir (entonces el aviso lleva el último mensaje del cliente)."""
    classify = getattr(runtime, "classify", None)
    if memory is None or not callable(classify):
        return ""
    entries = memory.get_history_entries(tenant_slug=tenant_slug, user_id=user_id)[-BRIEF_MESSAGES:]
    if not entries:
        return ""
    summary, _until = memory.get_summary(tenant_slug=tenant_slug, user_id=user_id)
    lines = [handoff_brief_writer.BRIEF_SUMMARY.format(summary=summary)] if summary else []
    lines.append(handoff_brief_writer.BRIEF_MESSAGES)
    lines += [f"{_ROLES.get(entry.get('role'), 'Cliente')}: {entry.get('text')}" for entry in entries]
    prompt = handoff_brief_writer.BRIEF_WRITER.format(reason=handoff_reason_text(reason if reason in HANDOFF_REASONS else "assistant"))
    try:
        raw = classify(prompt, user_message=redact_payment_values("\n".join(lines), runtime_yaml), bot_config=bot_config, max_tokens=200)
    except Exception as error:  # noqa: BLE001 - sin nota, el aviso lleva el último mensaje del cliente
        logger.warning("resumen_para_el_equipo_fallido", extra={"tenant": tenant_slug, "error": type(error).__name__})
        return ""
    note = " ".join(str(_json(raw).get("nota") or "").split())
    if not note:
        logger.warning("resumen_para_el_equipo_fallido", extra={"tenant": tenant_slug, "error": "formato"})
        return ""
    note = redact_payment_values(note, runtime_yaml)
    return note if len(note) <= MAX_BRIEF_CHARS else f"{note[: MAX_BRIEF_CHARS - 1].rstrip()}…"
