"""La nota para el equipo cuando un chat pasa a una persona (`application/pipeline/handoff_brief.py`).

Quien atiende llega sin haber leído el chat: la IA le escribe quién es el cliente y qué necesita. Aquí la IA tiene respuestas fijas:
se prueba cuándo se le pide la nota, qué recibe (nunca datos de pago), qué pasa si falla y que llega al canal. Qué tan buena es la nota
se mide con la IA real.
"""
from __future__ import annotations

import json
import logging

from app.application.pipeline.handoff_brief import MAX_BRIEF_CHARS, brief_for_team
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE, payment_values
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository
from pipeline_harness import reads, reply, run_conversation

SLUG, CUSTOMER = "saas", "573001112233"
NOTE = "Juan Camilo tiene una tienda de ropa, le interesa el Plan Básico y pidió hablar con una persona."


class _Writer:
    """La IA que escribe la nota, con una respuesta fija. Anota lo que recibió."""

    def __init__(self, answer: str | Exception = json.dumps({"nota": NOTE})):
        self.answer, self.calls = answer, []

    def classify(self, prompt, *, user_message, bot_config=None, max_tokens=0):
        self.calls.append((prompt, user_message))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def _memory(*texts: str) -> MemoryDomainService:
    memory = MemoryDomainService(MemoryRepository())
    for number, text in enumerate(texts):
        memory.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text=text, role="user" if number % 2 == 0 else "assistant")
    return memory


def _brief(writer, memory, reason="human_request"):
    return brief_for_team(
        writer, bot_config=None, memory=memory, runtime_yaml=load_tenant_runtime_yaml(SLUG), tenant_slug=SLUG, user_id=CUSTOMER, reason=reason
    )


def test_the_team_gets_a_note_written_from_the_conversation():
    writer = _Writer()
    memory = _memory("Hola, tengo una tienda de ropa", "¡Hola! ¿Qué te interesa?", "El Plan Básico", "Te cuento.", "Quiero hablar con una persona")
    assert _brief(writer, memory, "complaint") == NOTE
    (prompt, sent), = writer.calls
    assert "el cliente tiene un reclamo" in prompt and "No agregues nada que no haya dicho" in prompt and '{"nota": "..."}' in prompt
    assert "Cliente: Hola, tengo una tienda de ropa" in sent and "Cliente: Quiero hablar con una persona" in sent


def test_payment_data_never_reaches_the_note():
    number = next(value for value in payment_values(load_tenant_runtime_yaml(SLUG)) if value.isdigit())
    writer = _Writer(json.dumps({"nota": f"Pagó al {number} y quiere que lo verifiquen."}))
    note = _brief(writer, _memory(f"Ya pagué al {number}"), "payment_review")
    assert number not in writer.calls[0][1] and REDACTED_PAYMENT_VALUE in writer.calls[0][1]
    assert number not in note and REDACTED_PAYMENT_VALUE in note


def test_a_long_note_is_cut_and_a_failed_one_leaves_none(caplog):
    long_note = _Writer(json.dumps({"nota": "palabra " * 200}))
    note = _brief(long_note, _memory("Hola"))
    assert len(note) <= MAX_BRIEF_CHARS and note.endswith("…")
    with caplog.at_level(logging.WARNING, logger="assistant"):
        for answer in (RuntimeError("sin clave"), "no es json"):
            assert _brief(_Writer(answer), _memory("Hola")) == ""
    assert [record.message for record in caplog.records].count("resumen_para_el_equipo_fallido") == 2
    # Sin conversación no hay nada que resumir: no se gasta una llamada.
    empty = _Writer()
    assert _brief(empty, MemoryDomainService(MemoryRepository())) == "" and empty.calls == []


def test_the_engine_writes_the_note_only_when_the_chat_goes_to_a_person():
    """El motor completo: la lectura de pagos y la nota usan la misma IA simulada (cada una toma lo suyo del JSON fijo)."""
    fixed = {**reads(), "nota": NOTE}
    turns = [
        ("Hola, me interesa el Plan Básico", reply("¡Genial! Te cuento."), fixed),
        ("Quiero hablar con una persona", reply("Claro, te paso con alguien del equipo.", handoff="persona"), fixed),
    ]
    (first, second) = run_conversation(SLUG, turns, user_id="nota-equipo", with_context=True)
    assert "handoff_summary" not in first[1]
    assert second[1].get("handoff") is True and second[1].get("handoff_summary") == NOTE
