"""Pasar el chat a una persona del equipo lo decide la IA, no unas palabras de su mensaje.

Hasta el 13 nov 2026, si la IA escribía «te paso con…» el motor pausaba la IA y pasaba el chat al equipo, aunque ella no lo hubiera
decidido: con la IA real, el asesor describió un paso futuro («cuando pagues, te paso con el equipo para que activen tu sistema») y
el chat quedó esperando a una persona. Ahora:

- La IA decide con su señal (`metadata.handoff`: el cliente pide una persona o reclama). Un pago avisado también pasa al equipo.
- Ofrecer pasarlo no es pasarlo.
- Si su mensaje dice que lo pasa con el equipo y no lo marcó, se le pide otra respuesta, diciéndole por qué. Decide ella: si insiste
  sin marcarlo, no se pasa (como en el paso futuro de arriba), y queda el aviso `paso_a_persona_sin_marcar`.
- El paso de la conversación sale de hechos (el sistema envió los datos de pago), no de palabras: «Nequi» o «datos de arranque» en
  el mensaje de la IA ya no cambian nada.

Aquí la IA tiene respuestas fijas. Que decida bien se mide con la IA real (`experiments/quality_lab`, regla «pasa al equipo cuando debe»).
"""
from __future__ import annotations

from pipeline_harness import reads, reply, run_conversation

SLUG = "saas"


def _turn(message: str, answers, user_id: str):
    (answer, context), = run_conversation(SLUG, [(message, answers, reads())], user_id=user_id, with_context=True)
    return answer, context


def test_describing_a_future_step_is_not_handing_off():
    """El caso real (IA real, 13 nov 2026): el asesor describió lo que pasará después de pagar y el chat pasó al equipo."""
    future = reply("Cuando pagues, me envías el comprobante y te paso con el equipo para que activen tu sistema.", "info")
    answer, context = _turn("Cuando lo haga que nesesito hacer", [future, future], "paso-futuro")
    assert answer.startswith("Cuando pagues") and not context.get("handoff")


def test_offering_a_person_is_not_handing_off():
    offer = reply("Solo vendemos hamburguesas artesanales. Si prefieres, puedo pasarte con alguien de nuestro equipo.", "info")
    answer, context = _turn("Me llamo Juan Camilo", offer, "ofrece")
    assert answer.startswith("Solo vendemos") and not context.get("handoff")


def test_the_ai_decides_to_hand_off():
    decided = reply("Claro, te paso con alguien del equipo por este mismo chat.", "info", handoff="persona")
    _answer, context = _turn("Quiero hablar con una persona", decided, "decide")
    assert context.get("handoff") is True and context.get("handoff_reason") == "human_request"


def test_a_promise_without_the_decision_gets_another_answer():
    """Le dijo al cliente que lo pasa y no lo marcó: se le pide otra respuesta. Si en la segunda lo decide, pasa."""
    promise = reply("Te paso con alguien del equipo en un momento.", "info")
    marked = reply("Te paso con alguien del equipo en un momento.", "info", handoff="persona")
    (prompts, _answer), = run_conversation(SLUG, [("Necesito ayuda con mi cuenta", [promise, marked], reads())], user_id="promete")
    assert len(prompts) == 2 and "dice que lo pasas con el equipo, pero no lo marcaste" in prompts[1]
    (_answer, context), = run_conversation(SLUG, [("Necesito ayuda con mi cuenta", [promise, marked], reads())], user_id="promete-2", with_context=True)
    assert context.get("handoff") is True


def test_if_it_insists_without_deciding_its_decision_stands(caplog):
    import logging

    promise = reply("Te paso con alguien del equipo en un momento.", "info")
    with caplog.at_level(logging.WARNING, logger="assistant"):
        _answer, context = _turn("Necesito ayuda", [promise, promise], "insiste")
    assert not context.get("handoff")
    assert "paso_a_persona_sin_marcar" in [record.message for record in caplog.records]


def test_the_conversation_step_comes_from_facts_not_words():
    """«Nequi» o «datos de arranque» en el mensaje de la IA ya no cambian el paso de la conversación (ni lo que se le dice después)."""
    turns = [
        ("¿Cómo pago?", reply("Puedes pagar por Nequi o por transferencia. ¿Cuál prefieres?", "info"), reads()),
        ("¿Y después?", reply("Para activar te pido unos datos de arranque y te doy la guía de integración.", "info"), reads()),
        ("Ok", reply("Listo.", "info"), reads()),
    ]
    prompts = [turn_prompts[0] for turn_prompts, _ in run_conversation(SLUG, turns, user_id="sin-palabras")]
    for phrase in ("Venían avanzando por", "Ya iban dejando todo listo", "Ya iban coordinando"):
        assert all(phrase not in prompt for prompt in prompts), phrase
