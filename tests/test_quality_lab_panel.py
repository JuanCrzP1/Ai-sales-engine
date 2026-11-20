"""El estándar de lo que configura el negocio en el panel (`experiments/quality_lab/panel_standard.py`): los perfiles que se publican,
las conversaciones y las reglas exactas. Aquí no se llama a ninguna IA: se prueba que cada perfil es una configuración válida que el
motor compila y pone en el prompt, que la ficha del juez sale de lo compilado y que las reglas detectan lo que deben.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1] / "experiments" / "quality_lab"
sys.path.insert(0, str(LAB))

import panel_standard  # noqa: E402
from facts import business_facts  # noqa: E402
from standard import ENGINE_DATA, NO_DETAILS, conversations_for, judge_failures  # noqa: E402

from app.application.runtime import load_tenant_runtime_yaml  # noqa: E402
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService  # noqa: E402
from app.infrastructure.ai.prompting.business_model import detect_business_model  # noqa: E402
from pipeline_harness import publish_document  # noqa: E402

BLOCK = f"💳 *Datos para pagar*\n\n*Nequi*\n{ENGINE_DATA}\n\nCuando pagues, envíame aquí la captura del comprobante."


def _published(monkeypatch, tmp_path, slug: str) -> tuple[dict, str]:
    """El negocio publicado con su perfil del panel, como lo hace la puerta: la ficha del juez (de lo compilado) y el prompt."""
    profile = panel_standard.PROFILES[slug]
    publish_document(monkeypatch, tmp_path, slug, lambda document: document.update(panel_standard.publish(document, profile)))
    runtime = load_tenant_runtime_yaml(slug, channel="whatsapp")
    prompt, _metadata, _context = PromptBuilderService().build(client_config_id=slug, user_message="Hola", yaml_config=runtime, faq_results=[], progression_rules=None)
    return business_facts(runtime, detect_business_model(runtime)), prompt


def test_the_formal_profile_is_a_valid_config_and_reaches_the_prompt(monkeypatch, tmp_path):
    facts, prompt = _published(monkeypatch, tmp_path, "asesor_ai_prod")
    assert (facts["trato"], facts["emojis"], facts["max_palabras"], facts["estrategia_de_cierre"]) == ("formal", False, 40, "lead_capture")
    assert facts["tono"] == "profesional, sobrio y respetuoso"
    assert facts["horario"] == [{"days": ["lunes", "martes", "miercoles", "jueves", "viernes"], "opens": "08:00", "closes": "17:00"}]
    for said in ("Trata al cliente de usted en todo el mensaje", "Recuerda: trata al cliente de usted", "No uses emojis.", "Responde en máximo 40 palabras", "08:00 a 17:00", "el equipo lo contacta"):
        assert said in prompt, said


def test_the_casual_profile_is_its_opposite(monkeypatch, tmp_path):
    facts, prompt = _published(monkeypatch, tmp_path, "restaurant")
    assert (facts["trato"], facts["emojis"], facts["max_palabras"], facts["estrategia_de_cierre"]) == ("informal", True, 100, "checkout")
    for said in ("Trata al cliente de tú.", "Puedes usar algún emoji", "Responde en máximo 100 palabras", "12:00 a 22:00", "directo al pago"):
        assert said in prompt, said


def test_the_conversations_ask_for_a_closed_day_and_respect_how_the_business_closes(monkeypatch, tmp_path):
    facts, _prompt = _published(monkeypatch, tmp_path, "asesor_ai_prod")
    conversations = dict(conversations_for(facts, panel=True))
    assert list(conversations) == ["pregunta el horario", "decide comprar", "pide que le cuente todo"]
    assert conversations["pregunta el horario"][-1]["message"] == "¿Y el sábado abren?"
    assert "Me convence, lo quiero" in [turn["message"] for turn in conversations["decide comprar"]]
    # Captar datos: nadie pide los datos de pago, así que no le deben llegar en ningún turno.
    assert {turn["expect"] for turn in conversations["decide comprar"]} == {NO_DETAILS}


def test_with_checkout_the_payment_details_may_come(monkeypatch, tmp_path):
    facts, _prompt = _published(monkeypatch, tmp_path, "restaurant")
    conversations = dict(conversations_for(facts, panel=True))
    assert conversations["pregunta el horario"][-1]["message"] == "¿Y el lunes abren?"
    assert {turn["expect"] for turn in conversations["decide comprar"]} == {""}


FORMAL = {"max_palabras": 40, "emojis": False}


def _turn(reply: str, *, words: int | None = None, source: str = "ai", number: int = 2) -> dict:
    return {"turn": number, "message": "¿Qué incluye?", "reply": reply, "ai_words": words, "source": source}


def _broken(turns: list[dict], facts: dict) -> dict[str, list[int]]:
    return {rule: [failure["turn"] for failure in failures] for rule, failures in panel_standard.exact_failures(turns, facts).items() if failures}


def test_the_length_is_what_the_ai_wrote_before_the_engine_trims_it():
    assert _broken([_turn("Claro.", words=41)], FORMAL) == {"respeta_el_largo": [2]}
    assert _broken([_turn("Claro.", words=40)], FORMAL) == {}
    # Sin el conteo de la IA (una respuesta que no vino en su formato) no se juzga.
    assert _broken([_turn("Claro.", words=None)], FORMAL) == {}


@pytest.mark.parametrize("reply", ["Con gusto le ayudo 😊", "Perfecto ✅", "¡Listo! 🎉 Le cuento."])
def test_an_emoji_fails_when_the_business_does_not_want_them(reply):
    assert _broken([_turn(reply, words=4)], FORMAL) == {"sin_emojis_si_no_van": [2]}
    assert _broken([_turn(reply, words=4)], {**FORMAL, "emojis": True}) == {}


def test_the_platform_payment_message_and_the_fixed_welcome_do_not_count():
    assert _broken([_turn(f"Con gusto, aquí están los datos.\n\n{BLOCK}", words=6)], FORMAL) == {}
    assert _broken([_turn("Hola 👋 soy Juan", words=80, source="initial_message")], FORMAL) == {}
    # Tildes, eñes y signos de español no son emojis.
    assert _broken([_turn("¿Señora? ¡Qué bien! Atención: «sí».", words=5)], FORMAL) == {}


@pytest.mark.parametrize("reply", ["¿Te gustaría avanzar?", "Indícame tu nombre y teléfono.", "Tú decides.", "Tus datos quedan con el equipo."])
def test_tuteo_fails_only_when_the_business_is_formal(reply):
    """19 nov 2026: el juez dejó pasar «¿Te gustaría…?» y «tu nombre» con trato formal; la regla exacta no depende de su opinión."""
    assert _broken([_turn(reply, words=5)], {**FORMAL, "trato": "formal"}) == {"respeta_el_trato": [2]}
    assert _broken([_turn(reply, words=5)], {**FORMAL, "trato": "informal"}) == {}
    assert _broken([_turn(reply, words=5)], {**FORMAL, "trato": "neutral"}) == {}


def test_usted_fails_only_when_the_business_is_informal():
    assert _broken([_turn("¿Usted ya tiene cuenta?", words=4)], {**FORMAL, "trato": "informal"}) == {"respeta_el_trato": [2]}
    assert _broken([_turn("¿Usted ya tiene cuenta?", words=4)], {**FORMAL, "trato": "formal"}) == {}


def test_the_trato_rule_ignores_lookalikes_and_the_platform_payment_message():
    formal = {**FORMAL, "trato": "formal"}
    # «té», «Tunja», «tutorial», «antes», «ustedes» no son tuteo; el mensaje con los datos de pago es de la plataforma.
    assert _broken([_turn("Le recomiendo el té de Tunja; antes vea el tutorial.", words=9)], formal) == {}
    assert _broken([_turn(f"Con gusto, aquí están los datos.\n\n{BLOCK} Te confirmamos.", words=6)], formal) == {}
    assert _broken([_turn("¿Ustedes vienen juntos?", words=3)], {**FORMAL, "trato": "informal"}) == {}


def test_the_judge_only_counts_failures_with_the_advisor_quote():
    turns = [{"turn": 1, "message": "¿Qué incluye?", "reply": "Claro, te cuento lo que incluye."}]
    verdict = {"fallas": [
        {"regla": "trato_y_tono", "turno": 1, "cita": "Claro, te cuento", "razon": "tutea y el negocio es formal"},
        {"regla": "horario_del_negocio", "turno": 1, "cita": "atendemos los domingos", "razon": "inventa un día"},
        {"regla": "no_pide_lo_ya_dado", "turno": 1, "cita": "Claro, te cuento", "razon": "regla de otro estándar"},
    ]}
    failures, discarded = judge_failures(verdict, turns, panel_standard.JUDGE_RULES)
    assert failures == {"trato_y_tono": [{"turn": 1, "why": "tutea y el negocio es formal"}], "horario_del_negocio": [], "cierra_como_el_negocio": []}
    assert {item["rule"] for item in discarded} == {"horario_del_negocio", "no_pide_lo_ya_dado"}


def test_the_judge_reads_what_the_business_configured():
    facts = {"trato": "formal", "tono": "sobrio", "emojis": False, "max_palabras": 40, "horario": [{"days": ["lunes"], "opens": "08:00", "closes": "17:00"}],
             "estrategia_de_cierre": "lead_capture", "datos_que_pide": ["nombre"], "pagos_disponibles": {"nequi": True, "bank": False}}
    sheet = panel_standard.ficha(facts, {"nequi": "Nequi"})
    assert sheet["trato"] == "formal" and sheet["estrategia_de_cierre"] == "lead_capture" and sheet["medios_de_pago_del_negocio"] == ["Nequi"]
    # Cada regla del panel está en las instrucciones del juez.
    assert all(f"- {name}: {text}" in panel_standard.JUDGE for name, text in panel_standard.JUDGE_RULES.items())
