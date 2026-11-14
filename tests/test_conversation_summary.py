"""El resumen de lo que pasó antes en una conversación larga (`application/pipeline/conversation_summary.py`).

La IA ve los últimos mensajes; lo anterior le llega resumido. Aquí la IA que resume tiene respuestas fijas: se prueba cuándo se le pide
un resumen, qué recibe (nunca datos de pago), qué se guarda y que el asesor lo recibe. Qué tan bien resume se mide con la IA real.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from app.application.pipeline.conversation_summary import SUMMARY_BATCH, refresh_summary
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE, payment_values
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.ai.prompting.history import MAX_MESSAGES
from app.infrastructure.persistence.memory_repository import MemoryRepository
from pipeline_harness import reads, reply, run_conversation

SLUG, CUSTOMER = "saas", "573001112233"


class _Writer:
    """La IA que resume, con respuestas fijas. Anota lo que recibió."""

    def __init__(self, answer: str | Exception = '{"resumen": "Juan Camilo tiene una tienda de ropa y quiere el Plan Básico."}'):
        self.answer, self.calls = answer, []

    def classify(self, prompt, *, user_message, bot_config=None, max_tokens=0):
        self.calls.append((prompt, user_message))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def _conversation(memory: MemoryDomainService, count: int, *, start: int = 1, text: str = "mensaje {n}") -> None:
    for number in range(start, start + count):
        memory.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text=text.format(n=number), role="user" if number % 2 else "assistant")


def _refresh(writer, memory):
    return refresh_summary(writer, bot_config=None, memory=memory, runtime_yaml=load_tenant_runtime_yaml(SLUG), tenant_slug=SLUG, user_id=CUSTOMER)


def test_a_short_conversation_needs_no_summary():
    memory, writer = MemoryDomainService(MemoryRepository()), _Writer()
    _conversation(memory, MAX_MESSAGES + SUMMARY_BATCH - 1)
    assert _refresh(writer, memory) == "" and writer.calls == []


def test_what_the_ai_no_longer_sees_is_summarized_once_and_kept():
    memory, writer = MemoryDomainService(MemoryRepository()), _Writer()
    _conversation(memory, MAX_MESSAGES + SUMMARY_BATCH)
    summary = _refresh(writer, memory)
    assert summary == "Juan Camilo tiene una tienda de ropa y quiere el Plan Básico."
    (prompt, sent), = writer.calls
    assert '{"resumen": "..."}' in prompt and "No inventes nada" in prompt and "No escribas qué está pendiente" in prompt
    # Solo los mensajes que la IA ya no ve: no los últimos.
    assert "Cliente: mensaje 1\n" in sent and f"mensaje {SUMMARY_BATCH}" in sent and f"mensaje {SUMMARY_BATCH + 1}" not in sent
    stored, until = memory.get_summary(tenant_slug=SLUG, user_id=CUSTOMER)
    assert stored == summary and until is not None
    # El siguiente mensaje no vuelve a resumir: hace falta otro grupo de mensajes que la IA ya no vea.
    _conversation(memory, 1, start=100)
    assert _refresh(writer, memory) == summary and len(writer.calls) == 1


def test_the_next_summary_builds_on_the_previous_one():
    memory, writer = MemoryDomainService(MemoryRepository()), _Writer()
    _conversation(memory, MAX_MESSAGES + SUMMARY_BATCH)
    _refresh(writer, memory)
    _conversation(memory, SUMMARY_BATCH, start=100)
    writer.answer = '{"resumen": "Resumen nuevo."}'
    assert _refresh(writer, memory) == "Resumen nuevo."
    sent = writer.calls[-1][1]
    assert sent.startswith("Resumen anterior: Juan Camilo tiene una tienda de ropa") and "mensaje 1\n" not in sent


def test_payment_data_never_reaches_the_summary():
    runtime = load_tenant_runtime_yaml(SLUG)
    number = next(value for value in payment_values(runtime) if value.isdigit())
    memory = MemoryDomainService(MemoryRepository())
    _conversation(memory, MAX_MESSAGES + SUMMARY_BATCH, text=f"mensaje {{n}}: paga al {number}")
    writer = _Writer(json.dumps({"resumen": f"Le dimos el número {number}."}))
    summary = _refresh(writer, memory)
    assert number not in writer.calls[0][1] and REDACTED_PAYMENT_VALUE in writer.calls[0][1]
    assert number not in summary and summary == f"Le dimos el número {REDACTED_PAYMENT_VALUE}."


def test_if_the_summary_fails_the_previous_one_stays(caplog):
    memory = MemoryDomainService(MemoryRepository())
    memory.set_summary(tenant_slug=SLUG, user_id=CUSTOMER, summary="El anterior.", until=datetime.now(timezone.utc) - timedelta(days=1))
    _conversation(memory, MAX_MESSAGES + SUMMARY_BATCH)
    for answer in (RuntimeError("sin clave"), "no es json"):
        with caplog.at_level(logging.WARNING, logger="assistant"):
            assert _refresh(_Writer(answer), memory) == "El anterior."
    assert [record.message for record in caplog.records].count("resumen_fallido") == 2


def test_the_advisor_receives_the_summary_in_a_long_conversation():
    """El motor completo: en una conversación larga, a partir de cuando hay mensajes que la IA ya no ve, el asesor recibe el resumen."""
    # La IA que lee el pago y la que resume responden con el mismo JSON fijo: cada una toma lo suyo.
    fixed = {**reads(), "resumen": "Juan Camilo tiene una tienda de ropa y quiere el Plan Básico."}
    turns = [(f"mensaje {number}", reply(f"respuesta {number}"), fixed) for number in range(1, 16)]
    prompts = [turn_prompts[-1] for turn_prompts, _ in run_conversation(SLUG, turns, user_id="resumen-al-asesor")]
    fact = "Lo que contó el cliente antes de los últimos mensajes (resumen; si algo cambió después, manda lo reciente): Juan Camilo tiene una tienda de ropa y quiere el Plan Básico."
    assert fact not in prompts[0] and fact in prompts[-1]
