"""«Confirmar pago» en el chat: el mensaje que recibe el cliente y lo que sabe la IA después.

El recorrido completo por la API del panel (el envío una sola vez, la falla del canal, la venta, las pruebas) está en
`test_conversations_inbox.py`; que el mensaje sale de lo publicado, en `test_business_config_engine_integration.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.pipeline.payment_delivery import PAYMENT_CONFIRMED, confirmed_state, sent_state
from app.application.pipeline.payment_outcome import CONFIRMED, remember_confirmed_payment
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.conversations import ConversationSummary, PaymentClaim
from app.domain.business_config.payment_confirmation import DEFAULT_PAYMENT_CONFIRMED, payment_confirmed_message, payment_pending
from app.domain.conversation.memory import MemoryDomainService
from app.domain.operations.operational_renderer import render_op_anchor, render_op_rule
from app.domain.operations.operational_state import OperationalState
from app.infrastructure.ai.prompting import instructions
from app.infrastructure.persistence.memory_repository import MemoryRepository
from pipeline_harness import reads, reply, run_conversation, stored_document


def _config(**changes) -> BusinessConfig:
    document = stored_document("restaurant")
    document["messages"]["payment_confirmed"] = changes.pop("written", None)
    document.setdefault("response_style", {}).update(changes)
    return BusinessConfig.model_validate(document)


def test_the_customer_receives_the_message_the_business_wrote_as_it_is():
    assert payment_confirmed_message(_config(written="Recibimos tu pago 🙌, ya va tu pedido.", emojis=False)) == "Recibimos tu pago 🙌, ya va tu pedido."


def test_without_a_message_the_platform_one_follows_the_style_of_the_business():
    assert payment_confirmed_message(_config(formality="informal", emojis=True)) == "¡Listo! Tu pago quedó confirmado. Gracias por tu compra. ✅"
    assert payment_confirmed_message(_config(formality="formal", emojis=True)) == "¡Listo! Su pago quedó confirmado. Gracias por su compra. ✅"
    assert payment_confirmed_message(_config(formality="formal", emojis=False)) == "¡Listo! Su pago quedó confirmado. Gracias por su compra."
    # Sin nada publicado, el de la plataforma de tú.
    assert payment_confirmed_message(None) == DEFAULT_PAYMENT_CONFIRMED.tu


def _summary(reason: str | None, stage: str) -> ConversationSummary:
    now = datetime.now(timezone.utc)
    return ConversationSummary("c", "restaurant", "Restaurante", "whatsapp", "Ana", "open", now, now, None, 1, handoff_reason=reason, stage=stage)


def test_a_payment_is_pending_when_the_customer_reported_it_or_is_in_the_payment_stage():
    assert payment_pending(_summary("payment_review", "customer"))  # un cliente que vuelve a comprar
    assert payment_pending(_summary(None, "payment"))  # el equipo reanudó la IA sin confirmar
    assert not payment_pending(_summary("human_request", "ready"))
    assert not payment_pending(_summary(None, "customer"))
    assert PaymentClaim("payment_review", "payment").waited_for_payment and PaymentClaim(None, "payment").waited_for_payment
    assert not PaymentClaim("complaint", "payment").waited_for_payment


def test_once_confirmed_the_ai_knows_and_the_step_waiting_for_the_payment_ends():
    memory = MemoryDomainService(MemoryRepository())
    memory.set_payment_method(tenant_slug="restaurant", user_id="ana", method="nequi")
    memory.set_op_state(tenant_slug="restaurant", user_id="ana", state_dict=sent_state("nequi").to_dict())
    assert render_op_anchor(OperationalState.from_dict(memory.get_op_state(tenant_slug="restaurant", user_id="ana")))

    remember_confirmed_payment(memory, tenant_slug="restaurant", user_id="ana")
    assert memory.get_payment_status(tenant_slug="restaurant", user_id="ana") == CONFIRMED
    state = OperationalState.from_dict(memory.get_op_state(tenant_slug="restaurant", user_id="ana"))
    assert (state.pending_action, state.active_option) == (PAYMENT_CONFIRMED, "nequi")
    # Ya no «falta que pague y envíe el comprobante».
    assert render_op_anchor(state) == "" and render_op_rule(state) == ""
    assert confirmed_state("nequi").is_active()


def test_a_payment_the_advisor_marks_by_mistake_after_the_confirmation_does_not_undo_it():
    memory = MemoryDomainService(MemoryRepository())
    run_conversation("restaurant", [("Ya pagué", reply("Gracias, lo verificamos.", "buy", payment_status="reportado"))], user_id="ana", memory=memory)
    remember_confirmed_payment(memory, tenant_slug="restaurant", user_id="ana")
    # El asesor marca un pago, pero el lector entiende que el cliente no avisó ninguno: sigue confirmado.
    [(prompts, _)] = run_conversation(
        "restaurant", [("Gracias, ¿a qué hora llega?", reply("A las 3.", "info", payment_status="reportado"), reads())], user_id="ana", memory=memory,
    )
    assert instructions.PAYMENT_CONFIRMED in prompts[0]
    assert memory.get_payment_status(tenant_slug="restaurant", user_id="ana") == CONFIRMED


def test_if_the_memory_does_not_keep_it_the_team_is_told():
    """La memoria en la base, si no responde, sigue sin avisar: se comprueba lo guardado para que el panel lo diga."""

    class Forgetful(MemoryRepository):
        def set_payment_status(self, *, tenant_slug, user_id, status):
            return None

    with pytest.raises(RuntimeError, match="no guardó"):
        remember_confirmed_payment(MemoryDomainService(Forgetful()), tenant_slug="restaurant", user_id="ana")
