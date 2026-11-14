"""El estándar del asesor (`experiments/quality_lab/standard.py`): las conversaciones que se le hacen a la IA real y las reglas exactas de
pasa o no pasa. Aquí no se llama a ninguna IA: se prueba que las reglas detectan lo que deben, con respuestas escritas a mano (las del
chat real de producción del 13 nov 2026 y las del asesor ya corregido).
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1] / "experiments" / "quality_lab"
sys.path.insert(0, str(LAB))

from standard import (  # noqa: E402
    DETAILS,
    DETAILS_BY_NOW,
    ENGINE_DATA,
    EXACT_RULES,
    JUDGE,
    JUDGE_RULES,
    NO_DETAILS,
    REPORTED,
    conversations_for,
    exact_failures,
    has_details,
    confirm_request,
    judge_failures,
    keep_confirmed,
)

BLOCK = f"💳 *Datos para pagar*\n\n*Nequi*\n{ENGINE_DATA}\n\nCuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅"
FACTS = {"modelo": "saas", "oferta": [{"name": "el Plan Básico"}], "pagos_disponibles": {"link": True, "nequi": True, "daviplata": True, "bank": True, "breb": True}}


def _turns(*steps: tuple) -> list[dict]:
    return [{"turn": number, "message": message, "expect": expect, "reply": reply, "handoff": handoff}
            for number, (message, expect, reply, *rest) in enumerate(steps, start=1) for handoff in [bool(rest and rest[0])]]


def _broken(turns: list[dict]) -> dict[str, list[int]]:
    return {rule: [failure["turn"] for failure in failures] for rule, failures in exact_failures(turns).items() if failures}


def test_the_conversations_use_the_business_methods_and_the_real_production_chat():
    conversations = dict(conversations_for(FACTS))
    production = [(turn["message"], turn["expect"]) for turn in conversations["el chat de producción"]]
    assert production[:4] == [("Hola", ""), ("Me interesa el Plan Básico, quiero empezar", NO_DETAILS), ("Y puedo trasferir", NO_DETAILS), ("Y Nequi no", NO_DETAILS)]
    assert ("Te pago por Nequi", DETAILS_BY_NOW) in production and ("Pero se me borró el Nequi me lo envías de nuevo", DETAILS) in production
    assert production[-3:] == [("Cómo así", NO_DETAILS), ("Ya voy a pagar", NO_DETAILS), ("ya te consigné", REPORTED)]
    assert conversations["pide el medio con un error de escritura"][1]["message"] == "Pásame el nekui porfa"
    assert conversations["pide los datos de otro medio"][1]["message"] == "listo, mándame los datos para pagar por transferencia"
    # Un negocio con un solo medio no tiene «otro medio» por el que preguntar; sin medios, no hay estándar de pagos.
    only = dict(conversations_for({**FACTS, "pagos_disponibles": {"daviplata": True}}))
    assert "pide los datos de otro medio" not in only and only["el chat de producción"][2]["message"] == "Y Daviplata no"
    assert conversations_for({**FACTS, "pagos_disponibles": {}}) == []
    # Lo que cuenta el cliente de sí mismo va con el tipo de negocio: a un restaurante no le dice «es una tienda de ropa».
    messages = lambda facts: [turn["message"] for turn in dict(conversations_for(facts))["el chat de producción"]]  # noqa: E731
    assert "Me llamo Juan Camilo y es una tienda de ropa" in messages(FACTS) and "Me llamo Juan Camilo" in messages({**FACTS, "modelo": "catalog"})


def test_the_production_chat_of_november_13_does_not_pass():
    """Lo que pasó en producción: «Y puedo trasferir» → solo la cuenta; «Cómo así» → el mismo bloque otra vez."""
    turns = _turns(
        ("Y puedo trasferir", NO_DETAILS, BLOCK.replace("Nequi", "Bancolombia")),
        ("Te pago por Nequi", DETAILS_BY_NOW, BLOCK),
        ("Pero se me borró el Nequi me lo envías de nuevo", DETAILS, BLOCK),
        ("Cómo así", NO_DETAILS, BLOCK),
        ("ya te consigné", REPORTED, "Gracias. Le paso tu comprobante al equipo.", True),
    )
    assert _broken(turns) == {
        "el_asesor_habla": [1, 2, 3, 4],
        "sin_datos_sin_pedirlos": [1],
        "no_repite_el_bloque": [4],
        "no_repite_la_respuesta": [3, 4],
    }


def test_an_advisor_that_talks_and_sends_the_details_when_needed_passes():
    turns = _turns(
        ("Y puedo trasferir", NO_DETAILS, "¡Claro! Recibimos transferencia a Bancolombia. ¿Me compartes tu nombre?"),
        ("Te pago por Nequi", DETAILS_BY_NOW, f"¡Perfecto! Ahí abajo te dejo los datos.\n\n{BLOCK}"),
        ("Mi teléfono es 3157778899", "", "Listo, ya lo anoté."),
        ("Pero se me borró el Nequi me lo envías de nuevo", DETAILS, f"¡Claro! Aquí van otra vez.\n\n{BLOCK}"),
        # Nombrar el dato dentro de una frase no es repetir el bloque.
        ("Cómo así", NO_DETAILS, f"Te explico: pagas al Nequi {ENGINE_DATA} y me envías la captura."),
        ("ya te consigné", REPORTED, "¡Gracias! Lo paso al equipo.", True),
    )
    assert _broken(turns) == {}
    assert has_details(turns[1]["reply"]) and not has_details(turns[4]["reply"])


def test_each_exact_rule_catches_its_failure():
    assert _broken(_turns(("Pásame el Nequi", DETAILS, "Cuando lo hagas, avísame."))) == {"datos_cuando_los_necesita": [1]}
    assert _broken(_turns(("Te pago por Nequi", DETAILS_BY_NOW, "Dame tu teléfono primero."))) == {"datos_cuando_los_necesita": [1]}
    assert _broken(_turns(("Pásame el Nequi", DETAILS, "Usa este número [número de Nequi]."))) == {"datos_cuando_los_necesita": [1], "sin_marcadores": [1]}
    assert _broken(_turns(("Hola", "", "Hola, ¿en qué te ayudo?", True))) == {"pago_avisado_al_equipo": [1]}
    assert _broken(_turns(("ya te consigné", REPORTED, "¡Gracias!"))) == {"pago_avisado_al_equipo": [1]}
    # El teléfono del cliente dado como Nequi (13 nov 2026); anotarlo no es darlo como dato de pago.
    assert _broken(_turns(("Cómo así", NO_DETAILS, "Paga a ese número de Nequi 315 777 8899."))) == {"sin_numeros_de_pago_falsos": [1]}
    assert _broken(_turns(("Mi teléfono es 3157778899", "", "Anoté tu teléfono 3157778899."))) == {}


def test_the_judge_is_asked_one_verdict_per_rule():
    assert set(EXACT_RULES).isdisjoint(JUDGE_RULES)
    assert all(f"- {name}: " in JUDGE for name in JUDGE_RULES)
    assert '"fallas"' in JUDGE and '"cita"' in JUDGE and ENGINE_DATA in JUDGE


def test_a_judge_failure_without_its_proof_does_not_count():
    """Con el juez real (13 nov 2026): marcó «pide lo ya dado» en 6 de 18 conversaciones sin que el cliente hubiera dado antes ese
    dato, y «no pasa» con una razón que decía que sí. Ahora una falla solo vale con la frase textual del asesor (y, en esa regla, con
    la del cliente en un turno anterior)."""
    turns = _turns(("Hola", "", "Hola"), ("Me llamo Juan", "", "Gracias, Juan"), ("Te pago por Nequi", "", "Perfecto. ¿Cuál es tu nombre?"))

    def judged(*items: dict):
        return judge_failures({"fallas": list(items)}, turns)

    asked_again = {"regla": "no_pide_lo_ya_dado", "turno": 3, "cita": "¿cuál es tu nombre?", "razon": "pide el nombre otra vez"}
    failures, discarded = judged({**asked_again, "cita_cliente": "Me llamo Juan"})
    assert failures["no_pide_lo_ya_dado"] == [{"turn": 3, "why": "pide el nombre otra vez"}] and not discarded
    # Sin la frase del cliente, con una que no dijo o con una frase del asesor que no está en ese turno, la falla se descarta.
    for broken in (asked_again, {**asked_again, "cita_cliente": "mi nombre es Pedro"}, {**asked_again, "cita": "dame tu nombre", "cita_cliente": "Me llamo Juan"},
                   {**asked_again, "turno": 2, "cita_cliente": "Me llamo Juan"}, {**asked_again, "regla": "otra_regla"}):
        failures, discarded = judged(broken)
        assert not any(failures.values()) and len(discarded) == 1, broken
    # Las demás reglas solo necesitan la frase del asesor.
    failures, _ = judged({"regla": "explica_cuando_no_entienden", "turno": 3, "cita": "Perfecto.", "razon": "no explica"})
    assert failures["explica_cuando_no_entienden"] == [{"turn": 3, "why": "no explica"}]
    # Sin fallas, todo pasa; sin veredicto, nada se da por bueno.
    assert not any(judged()[0].values())
    assert all(items == [{"turn": 0, "why": "el juez no dio veredicto"}] for items in judge_failures({}, turns)[0].values())


def test_only_the_failures_a_second_look_confirms_count():
    turns = _turns(("¿Tienen Nequi?", "", "Sí, aceptamos Nequi. ¿Te envío los datos?"), ("Cómo así", "", "¿Te los envío de nuevo?"))
    reported = {"responde_lo_que_preguntan": [{"turn": 1, "why": "ignora la pregunta"}], "explica_cuando_no_entienden": [{"turn": 2, "why": "no explica"}],
                "no_pide_lo_ya_dado": [{"turn": 0, "why": "el juez no dio veredicto"}]}
    asked = []

    def confirm(rule, conversation, failure):
        asked.append(confirm_request(rule, conversation, failure))
        return rule == "explica_cuando_no_entienden"

    kept, dropped = keep_confirmed(reported, turns, confirm)
    assert kept == {"responde_lo_que_preguntan": [], "explica_cuando_no_entienden": [{"turn": 2, "why": "no explica"}],
                    "no_pide_lo_ya_dado": [{"turn": 0, "why": "el juez no dio veredicto"}]}
    assert dropped == [{"turn": 1, "why": "ignora la pregunta", "rule": "responde_lo_que_preguntan"}]
    # El segundo revisor ve la regla y la conversación solo hasta ese turno.
    assert len(asked) == 2 and "Cómo así" not in asked[0] and asked[0].startswith("REGLA (responde_lo_que_preguntan): ")
    assert "FALLA REPORTADA en el turno 2: no explica" in asked[1]
