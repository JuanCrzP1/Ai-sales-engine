"""El estándar de «Cuándo pasar a una persona»: con las reglas que configuró el negocio, ¿pasa el chat cuando debe y solo entonces?

Con `--escalation`, la puerta (`run_standard_gate.py`) publica en la copia aislada los negocios con `PROFILE` y corre estas
conversaciones en lugar de las de pagos. Las reglas son instrucciones para la IA (`prompting/sections/escalation.py`): aquí se mide,
con la IA real, que las siga.

- Pide una persona: primero le ofrece resolverlo (sin pasarlo); si insiste, lo pasa.
- Pregunta por un tema que atiende el equipo: lo pasa.
- Pregunta por un tema que resuelve el asistente: no lo pasa.
- La conversación se estanca: a la tercera queja, ya lo pasó.
"""
from __future__ import annotations

# Las reglas con las que se publica el negocio en la corrida (las mismas que podría escribir en el panel).
PROFILE = {
    "on_request": "offer_help_first",
    "always_topics": ["reembolsos y devoluciones de dinero"],
    "never_topics": ["descuentos y promociones"],
    "when_stuck": True,
}

# Como el negocio real en producción (14 nov 2026): un mensaje propio para cuando pasa el chat a una persona y «pasar a una persona»
# como forma de cierre. Con ellos, la IA usaba ese mensaje apenas el cliente pedía una persona, aunque el negocio pidiera ofrecer ayuda
# primero; sin ellos, la puerta no lo veía.
HANDOFF_MESSAGE = "Te paso con alguien del equipo por este mismo chat. En un momento te escriben."

# Lo que se espera de un turno, además de los del estándar de pagos (`standard.py`): que no lo pase y le ofrezca resolverlo
# (`OFFERS_HELP`), que a esa altura ya lo haya pasado (`HANDOFF_BY_NOW`) o que pueda pasarlo o no (`MAY_HANDOFF`).
OFFERS_HELP, HANDOFF_BY_NOW, MAY_HANDOFF = "ofrece_ayuda", "pasa_a_esta_altura", "puede_pasar"

JUDGE_RULE = (
    "Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. Con «offer_help_first», la primera vez que el cliente "
    "pide una persona el asesor le ofrece resolverlo él, en una frase y sin insistir ni negarse a pasarlo. En un tema de "
    "«always_topics» no lo resuelve él: dice que lo pasa con el equipo (no inventa la política). En un tema de «never_topics» le "
    "responde él. Con «when_stuck» en true, pasar el chat cuando el cliente se frustra o repite lo mismo cumple. Sin esas reglas "
    "en la ficha, no aplica."
)


def conversations(facts: dict, handoff: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Las conversaciones del estándar de paso a persona para ese negocio: (nombre, [(mensaje del cliente, qué se espera)])."""
    offer = facts["oferta"][0]["name"] if facts["oferta"] else "lo que ofrecen"
    start = (f"Hola, me interesa {offer}", "")
    return [
        ("pide una persona y luego insiste", [start, ("Quiero hablar con una persona", OFFERS_HELP), ("No, gracias, prefiero que me atienda una persona", handoff)]),
        ("pregunta por un tema del equipo", [start, ("Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?", handoff)]),
        ("pregunta por un tema que resuelve el asistente", [start, ("¿Tienen algún descuento o promoción?", "")]),
        (
            "la conversación se estanca",
            [
                start,
                ("No entiendo nada de lo que me dices", MAY_HANDOFF),
                ("Sigo sin entender, ya te lo pregunté y no me ayudas", MAY_HANDOFF),
                ("Esto no me sirve, ya me cansé de preguntar lo mismo", HANDOFF_BY_NOW),
            ],
        ),
    ]
