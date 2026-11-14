"""¿Cuadra lo que dice la IA con lo que decidió sobre pasar el chat a una persona del equipo?

Pasar el chat a una persona lo decide la IA con su señal (`metadata.handoff`: el cliente pide una persona o reclama) y un pago
avisado (lo entiende el lector de pagos). Las palabras de su mensaje no deciden nada: hasta el 13 nov 2026, «te paso con…» en el
mensaje pasaba el chat al equipo aunque la IA describiera un paso futuro («cuando pagues, te paso con el equipo para que activen tu
sistema») y el cliente quedaba esperando a una persona.

Lo que sí se revisa es que su mensaje no le diga al cliente algo distinto de lo que decidió: si dice que lo pasa con el equipo y no lo
marcó, se le pide otra respuesta, diciéndole por qué (`ai_execution.py`). Decide ella otra vez; si insiste sin marcarlo, manda su
decisión y queda el aviso `paso_a_persona_sin_marcar`. Ofrecer pasarlo («si prefieres, puedo pasarte con alguien») no es pasarlo.
"""
from __future__ import annotations

import re

# Le dice al cliente que lo pasa con el equipo: «te paso con alguien», «te comunico con un asesor», «alguien del equipo te escribe».
_SAYS_IT_HANDS_OFF = re.compile(
    r"\b(te|lo|la)\s+(paso|pongo|conecto|comunico|transfiero|remito)\s+con\b|"
    r"\b(alguien del equipo|un asesor|una persona del equipo)\s+te\s+(va a\s+)?(escrib|contact|atiend|respond)\w*",
    re.IGNORECASE,
)
# Se lo ofrece, sin decidirlo: «si prefieres…», «¿quieres que te pase…?», «puedo pasarte…».
_OFFERS_IT = re.compile(r"\bsi (prefieres|quieres|deseas|gustas)\b|¿\s*(quieres|prefieres|deseas|te gustar[ií]a)\b|\bpuedo pasarte\b", re.IGNORECASE)

# Por qué se le pide otra respuesta (`answer_again` en el prompt).
UNMARKED = "handoff_unmarked"


def handoff_problem(response_text: str, metadata: dict) -> dict:
    """`{"handoff_unmarked": True}` si el mensaje le dice al cliente que lo pasa con el equipo y la IA no lo decidió; `{}` si cuadra."""
    if str((metadata or {}).get("handoff") or "").strip():
        return {}
    text = str(response_text or "")
    return {UNMARKED: True} if _SAYS_IT_HANDS_OFF.search(text) and not _OFFERS_IT.search(text) else {}
