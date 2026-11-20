"""Los textos que escribe la plataforma (no la IA) van con el trato del negocio: de usted si es formal, de tú en los demás casos.

Hasta el 19 nov 2026 todos estaban de tú: un negocio que trataba de usted recibía «Cuando pagues, envíame aquí la captura…» justo
debajo de una respuesta de usted. Aquí se prueban por el camino real (el negocio publicado y el motor que lo lee): el mensaje con
los datos de pago, la pregunta del medio, las frases cuando la IA no puede enviar los datos, el mensaje cuando la IA falla o pasa
a una persona sin escribir, y el ejemplo que lee la IA cuando el cliente no entiende qué sigue. Los avisos de espera están en
`test_human_attention.py`.
"""
from __future__ import annotations

import pytest

from app.application.ai_pipeline import AIPipeline
from app.application.pipeline.fallback import PLATFORM_FALLBACK_REPLY
from app.application.pipeline.payment_delivery import deliver
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.business_config.formality import Phrase, formality_of
from app.domain.business_config.payment_accounts import which_method_question
from app.domain.conversation.memory import MemoryDomainService
from app.domain.operations.operational_renderer import render_op_rule
from app.domain.operations.operational_state import OperationalState
from app.infrastructure.ai.ai_orchestrator import FAILED_REPLY, HANDOFF_WITHOUT_TEXT
from app.infrastructure.persistence.memory_repository import MemoryRepository
from pipeline_harness import publish_document, reply, run_conversation

SLUG = "saas"
TALKS = {"formal": "usted", "informal": "tu", "neutral": "tu", None: "tu"}


def _with(formality: str | None, **messages):
    def mutate(document: dict) -> None:
        document["response_style"]["formality"] = formality
        document["messages"].update(messages)
    return mutate


def _cash_only(formality: str | None):
    def mutate(document: dict) -> None:
        _with(formality)(document)
        profile = document["payments"][0]
        profile["transfer_methods"] = [{"type": "cash"}]
        profile["link_enabled"] = False
    return mutate


def test_only_formal_changes_a_platform_text():
    phrase = Phrase(tu="¿Quieres?", usted="¿Quiere?")
    assert [phrase.to(value) for value in ("formal", "informal", "neutral", "", None)] == ["¿Quiere?", "¿Quieres?", "¿Quieres?", "¿Quieres?", "¿Quieres?"]
    assert formality_of({"config": {"profile": {"formality": "formal"}}}) == "formal"
    assert formality_of({"config": {"profile": {}}}) == formality_of({"config": None}) == formality_of(None) == ""


@pytest.mark.parametrize("formality", TALKS)
def test_the_payment_details_speak_like_the_business(monkeypatch, tmp_path, formality):
    publish_document(monkeypatch, tmp_path, SLUG, _with(formality))
    ((_prompts, answer),) = run_conversation(SLUG, [("Te pago por Nequi", reply("Listo.", "buy", send_payment="nequi"))], user_id=f"pago-{formality}")
    expected = {
        "usted": "Cuando pague, envíeme aquí la captura del comprobante y le confirmamos. ✅",
        "tu": "Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅",
    }[TALKS[formality]]
    assert "💳 *Datos para pagar*\n\n*Nequi*\n" in answer and answer.endswith(expected)


@pytest.mark.parametrize("formality", ["formal", "informal"])
def test_cash_without_instructions_speaks_like_the_business(monkeypatch, tmp_path, formality):
    publish_document(monkeypatch, tmp_path, SLUG, _cash_only(formality))
    ((_prompts, answer),) = run_conversation(SLUG, [("Pago en efectivo", reply("Listo.", "buy", send_payment="efectivo"))], user_id=f"efectivo-{formality}")
    if formality == "formal":
        assert "Paga en efectivo al recibir su pedido." in answer and answer.endswith("Cualquier duda, escríbame por aquí. ✅")
    else:
        assert "Pagas en efectivo al recibir tu pedido." in answer and answer.endswith("Cualquier duda, escríbeme por aquí. ✅")


def test_a_template_written_by_the_business_is_never_changed(monkeypatch, tmp_path):
    own = "Datos: {datos}\nCuando pagues, avísame."
    publish_document(monkeypatch, tmp_path, SLUG, _with("formal", payment_details=own))
    ((_prompts, answer),) = run_conversation(SLUG, [("Te pago por Nequi", reply("Listo.", "buy", send_payment="nequi"))], user_id="propia")
    assert answer.endswith("Cuando pagues, avísame.") and "envíeme" not in answer


def test_the_payment_questions_and_rescues_speak_like_the_business(monkeypatch, tmp_path):
    publish_document(monkeypatch, tmp_path, SLUG, _with("formal"))
    runtime = load_tenant_runtime_yaml(SLUG)
    assert which_method_question(runtime).startswith("¿Con qué medio prefiere pagar: ")
    # La IA dijo (dos veces) que no podía enviar los datos: sale una frase de la plataforma, que sí es verdad.
    refusal = "No puedo enviarte el número de Nequi."
    offered = deliver(refusal, runtime, asked=False)
    assert offered.lead == "Claro, puede pagar por Nequi. ¿Quiere que le envíe los datos?" and not offered.details
    sent = deliver(refusal, runtime, asked=True, asked_method="nequi")
    assert sent.lead == "Le dejo aquí los datos para pagar por Nequi." and sent.details
    publish_document(monkeypatch, tmp_path / "tu", SLUG, _with("informal"))
    runtime = load_tenant_runtime_yaml(SLUG)
    assert which_method_question(runtime).startswith("¿Con qué medio prefieres pagar: ")
    assert deliver(refusal, runtime, asked=False).lead == "Claro, puedes pagar por Nequi. ¿Quieres que te envíe los datos?"


def test_when_the_ai_fails_or_hands_off_without_writing_the_platform_speaks_like_the_business(monkeypatch, tmp_path):
    publish_document(monkeypatch, tmp_path, SLUG, _with("formal"))
    turns = [("Necesito información", reply("Claro, le cuento.")), ("¿Y cuánto cuesta?", reply("", "info"))]
    (_first, (failed, _context)) = run_conversation(SLUG, turns, user_id="falla", with_context=True)
    assert failed == FAILED_REPLY.usted
    ((handed, context),) = run_conversation(SLUG, [("Quiero una persona", reply("", "info", handoff="persona"))], user_id="pasa", with_context=True)
    assert handed.startswith(HANDOFF_WITHOUT_TEXT.usted) and context.get("handoff") is True
    # Sin clave de IA: el mensaje de respaldo de la plataforma (el negocio no escribió el suyo).
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=lambda _slug: None)
    answer = pipeline.run(
        tenant=type("T", (), {"slug": SLUG, "name": SLUG, "id": SLUG})(), user_message="¿Cuánto cuesta?", user_id="respaldo",
        bot_config=None, conversation_history=[], faq_results=[], yaml_config=None,
    )
    assert answer == (PLATFORM_FALLBACK_REPLY.usted, False)


def test_the_example_the_ai_reads_after_the_payment_details_speaks_like_the_business():
    """La IA copia los ejemplos tal cual: con «Te explico: arriba te dejé…», un negocio de usted recibiría esa frase."""
    sent = OperationalState(active_process="payment", active_option="nequi", pending_action="report_payment")
    assert "«Le explico: arriba, en este chat, le dejé los datos para pagar. Hace el pago" in render_op_rule(sent, "formal")
    assert "«Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago" in render_op_rule(sent, "neutral")
    cash = OperationalState(active_process="payment", active_option="cash", pending_action="report_payment")
    assert "«Le explico: arriba le dejé cómo pagar en efectivo. Sigue esos pasos" in render_op_rule(cash, "formal")
