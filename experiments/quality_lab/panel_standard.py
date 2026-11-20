"""El estándar de «lo que configura el negocio en el panel»: ¿la IA lo obedece? El trato y el tono, el largo de las respuestas, los
emojis, el horario y la forma de cerrar la venta.

Las pruebas del motor comprueban que cada ajuste llega al prompt (`tests/test_business_config_engine_integration.py`); no que la IA
lo cumpla. Con `--panel`, la puerta (`run_standard_gate.py`) publica en la copia aislada cada negocio con su perfil (`PROFILES`), como
lo haría el negocio en el panel, y corre estas conversaciones con la IA real. Los dos perfiles son opuestos a propósito: si la IA
respondiera igual con cualquier ajuste, una de las dos mitades no pasaría.

- Reglas exactas (se cuentan, sin opinión): el largo de lo que escribe la IA y los emojis cuando el negocio no los quiere.
- Reglas del juez: el trato y el tono, el horario y la forma de cerrar. El juez lee los ajustes que quedaron publicados (la ficha sale
  de lo que compiló el motor, no de `PROFILES`).
"""
from __future__ import annotations

import re

from standard import NO_DETAILS, details_of

# Lo que el negocio configura en el panel, por negocio de ejemplo. Opuestos: usted y sin emojis, respuestas cortas, de lunes a viernes y
# cerrar captando los datos; frente a tú y con emojis, respuestas detalladas, de martes a domingo y cerrar enviando el pago.
PROFILES = {
    "asesor_ai_prod": {
        "response_style": {"tone": "profesional, sobrio y respetuoso", "formality": "formal", "emojis": False, "length": "short", "max_words": 40},
        "opening_hours": [{"days": ["lunes", "martes", "miercoles", "jueves", "viernes"], "opens": "08:00", "closes": "17:00"}],
        "closing_strategy": "lead_capture",
    },
    "restaurant": {
        "response_style": {"tone": "cercano, alegre y entusiasta", "formality": "informal", "emojis": True, "length": "long", "max_words": 100},
        "opening_hours": [{"days": ["martes", "miercoles", "jueves", "viernes", "sabado", "domingo"], "opens": "12:00", "closes": "22:00"}],
        "closing_strategy": "checkout",
    },
}

WEEKDAYS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
_SAID_DAY = {"miercoles": "miércoles", "sabado": "sábado"}


def publish(document: dict, profile: dict) -> dict:
    """El documento del negocio con los ajustes del perfil, como los guarda el panel: estilo de respuesta, horario y forma de cerrar.
    Lo demás del estilo (la voz, las indicaciones) queda como estaba."""
    document = {**document}
    document["response_style"] = {**document.get("response_style", {}), **profile["response_style"]}
    document["identity"] = {**document["identity"], "opening_hours": profile["opening_hours"]}
    document["sales"] = {**document["sales"], "closing": {**document["sales"]["closing"], "strategy": profile["closing_strategy"]}}
    return document


def closed_day(facts: dict) -> str:
    """Un día en que el negocio no atiende, para preguntarle por él ("" si atiende todos)."""
    open_days = {day for hours in facts.get("horario") or [] for day in hours.get("days") or []}
    return next((day for day in WEEKDAYS if day not in open_days), "")


def conversations(facts: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    """Las conversaciones del estándar del panel para ese negocio: (nombre, [(mensaje del cliente, qué se espera)]).

    Con «captar datos», nada de lo que dice el cliente pide los datos de pago: no le deben llegar (`NO_DETAILS`)."""
    offer = facts["oferta"][0]["name"] if facts["oferta"] else "lo que ofrecen"
    quiet = NO_DETAILS if facts.get("estrategia_de_cierre") == "lead_capture" else ""
    start = (f"Hola, me interesa {offer}", quiet)
    day = closed_day(facts)
    return [
        ("pregunta el horario", [start, ("¿En qué horario atienden?", quiet),
                                 *([(f"¿Y el {_SAID_DAY.get(day, day)} abren?", quiet)] if day else [])]),
        ("decide comprar", [start, (f"¿Cuánto cuesta {offer}?", quiet), ("Me convence, lo quiero", quiet), ("Me llamo Ana", quiet)]),
        ("pide que le cuente todo", [(f"Hola, cuéntame todo sobre {offer}: qué incluye, cómo funciona y por qué me conviene", quiet),
                                     ("¿Y qué más tienen?", quiet)]),
    ]


EXACT_RULES = {
    "respeta_el_largo": "Lo que escribe la IA no pasa del máximo de palabras del negocio, sin que el motor tenga que recortarlo.",
    "sin_emojis_si_no_van": "Si el negocio no quiere emojis, el asesor no usa ninguno (el mensaje con los datos de pago es de la plataforma).",
    "respeta_el_trato": "Con trato formal el asesor no tutea («tú», «te», «ti», «contigo», «tu», «tus»); con informal no dice «usted».",
}

# Las palabras que delatan el trato sin duda: con usted nunca se dice «te» ni «tu», y con tú nunca «usted». Las formas del verbo
# («quieres», «cuénteme») dependen de la frase: esas las revisa el juez (`trato_y_tono`). La primera medición (19 nov 2026) mostró
# que el juez solo vio una parte: dejó pasar «¿Te gustaría…?» y «tu nombre» en conversaciones que dio por buenas.
_TUTEO = re.compile(r"\b(tú|te|ti|contigo|tu|tus)\b", re.IGNORECASE)
_USTED = re.compile(r"\busted\b", re.IGNORECASE)

# Emojis: pictogramas, símbolos y banderas. No cuenta la puntuación ni las letras con tilde.
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF\U0000FE0F]")


def _words(text: str) -> int:
    return len(str(text or "").split())


def exact_failures(turns: list[dict], facts: dict) -> dict[str, list[dict]]:
    """Por cada regla exacta del panel, los turnos donde no pasa: `{"turn", "why"}`. El saludo fijo del negocio (sin IA) no cuenta."""
    failures: dict[str, list[dict]] = {name: [] for name in EXACT_RULES}
    limit = facts.get("max_palabras")
    for turn in turns:
        if turn.get("source") == "initial_message":
            continue
        said = str(turn.get("reply") or "")
        block = details_of(said)
        if block:
            # El mensaje con los datos de pago lo pone la plataforma: cuenta solo lo que escribió el asesor antes de él.
            said = said[: said.find(block.splitlines()[0])]
        written = turn.get("ai_words")
        if isinstance(limit, int) and isinstance(written, int) and written > limit:
            failures["respeta_el_largo"].append({"turn": turn["turn"], "why": f"la IA escribió {written} palabras y el máximo es {limit}"})
        if facts.get("emojis") is False and _EMOJI.search(said):
            failures["sin_emojis_si_no_van"].append({"turn": turn["turn"], "why": "usó un emoji y el negocio no los quiere"})
        wrong = _TUTEO if facts.get("trato") == "formal" else _USTED if facts.get("trato") == "informal" else None
        found = sorted({word.lower() for word in wrong.findall(said)}) if wrong else []
        if found:
            failures["respeta_el_trato"].append({"turn": turn["turn"], "why": f"el trato es {facts['trato']} y dijo «{'», «'.join(found)}»"})
    return failures


JUDGE_RULES = {
    "trato_y_tono": (
        "El asesor trata al cliente como dice «trato» en la ficha: «formal» es siempre de usted («usted», «su», «le», «cuénteme», "
        "«compártame», «¿le gustaría…?»; nunca «tú», «te», «tu», «quieres», «cuéntame», «compárteme», ni mezclas como «compárteme su "
        "nombre»); «informal» es de tú; «neutral», amable y respetuoso. Y habla con el «tono» de la ficha. No pasa si cambia el trato en "
        "algún mensaje o si su tono contradice el de la ficha (por ejemplo, frío cuando debe ser alegre, o con jerga cuando debe ser "
        "sobrio)."
    ),
    "horario_del_negocio": (
        "Cuando el cliente pregunta por el horario o por un día, el asesor da el de la ficha («horario»): los días y las horas correctos; "
        "si pregunta por un día que no está en el horario, le dice que ese día no atienden. No pasa si inventa o cambia un día o una "
        "hora, si dice que atiende un día que no está, o si no responde la pregunta."
    ),
    "cierra_como_el_negocio": (
        "Cuando el cliente decide comprar («lo quiero»), el asesor cierra como dice «estrategia_de_cierre» en la ficha. «lead_capture»: "
        "le pide los datos que faltan y le dice que el equipo lo contacta para continuar; no le pide que pague ni le ofrece medios de "
        "pago (salvo que el cliente lo pida). «checkout»: lo lleva a pagar de una vez (le dice cómo pagar o le ofrece los medios de "
        "pago) y le pide solo los datos que hacen falta, sin alargar con más preguntas. «direct_sale»: confirma lo que lleva y después "
        "le pide los datos y le dice cómo pagar. No pasa si cierra de otra forma."
    ),
}
JUDGE = (
    "Eres auditor de calidad de un asesor de ventas por chat. El negocio configuró cómo debe atender (la FICHA): revisa si el asesor "
    "lo cumple. Sé estricto pero justo: reporta una falla solo si puedes copiar la frase exacta del asesor que la muestra. Si una "
    "regla no aplica o se cumple, no la reportes.\n"
    "«[dato entregado por el motor]» es un dato de pago real que el sistema le envió al cliente.\n\n"
    "REGLAS:\n"
    + "\n".join(f"- {name}: {text}" for name, text in JUDGE_RULES.items())
    + '\n\nDevuelve SOLO JSON: {"fallas": [{"regla": "<nombre de la regla>", "turno": <número del turno>, "cita": "<frase copiada tal '
    'cual del mensaje del asesor en ese turno>", "razon": "máximo 15 palabras"}]}. Sin fallas: {"fallas": []}.'
)
CONFIRM = (
    "Revisas si una falla reportada en una conversación de ventas por chat es real. El negocio configuró cómo debe atender (la FICHA). "
    "Lee la regla, la ficha y la conversación hasta ese turno. Confirma solo si la última respuesta del asesor de verdad incumple esa "
    "regla según la ficha; si la cumple o la regla no aplica, no la confirmes.\n"
    'Devuelve SOLO JSON: {"confirmada": true, "razon": "máximo 15 palabras"}'
)


def ficha(facts: dict, method_names: dict[str, str]) -> dict:
    """Lo que el juez necesita saber de lo que configuró el negocio (lo publicado, como lo compiló el motor)."""
    return {
        "trato": facts.get("trato") or "sin indicar",
        "tono": facts.get("tono") or "",
        "emojis": facts.get("emojis"),
        "max_palabras": facts.get("max_palabras"),
        "horario": facts.get("horario") or [],
        "estrategia_de_cierre": facts.get("estrategia_de_cierre") or "",
        "datos_que_pide": facts.get("datos_que_pide") or [],
        "medios_de_pago_del_negocio": [method_names.get(kind, kind) for kind, has in facts["pagos_disponibles"].items() if has],
    }
