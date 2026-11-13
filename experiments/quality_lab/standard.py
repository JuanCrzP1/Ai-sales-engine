"""El estándar del asesor: lo que debe pasar siempre en los momentos de pago, como pruebas de pasa o no pasa.

Es lo que pidió el dueño del producto el 13 nov 2026, con su chat real de producción: un asesor que habla y guía, no un bot de
preguntas frecuentes. No da una nota promedio: cada regla pasa o no pasa en cada conversación, y un cambio se publica solo si pasan
todas (`run_standard_gate.py`). La nota promedio del juez (`run_quality_eval.py`) premiaba la plantilla sola, que es justo lo que el
estándar rechaza: por eso las dos mediciones son distintas.

- `conversations_for(facts)`: las conversaciones, con la oferta y los medios de pago reales del negocio.
- `exact_failures(turns)`: las reglas que se comprueban sin opinión.
- `JUDGE_RULES` y `JUDGE`: las reglas que necesitan leer la conversación; el juez responde pasa o no pasa en cada una
  (`judge_failures` lee su veredicto y descarta las fallas sin prueba).
"""
from __future__ import annotations

import re

# Con lo que el laboratorio oculta el dato de pago real que entregó el motor (`capture.py`).
ENGINE_DATA = "[dato entregado por el motor]"
# Así empieza el mensaje con los datos de pago (la plantilla de la plataforma).
_DETAILS_START = ("💳", "💵")
_PLACEHOLDER = re.compile(r"\[[^\[\]\n]{1,60}\](?!\()")
# Cómo nombra el cliente cada medio, y cómo pregunta por él sin signos de pregunta (así escribe la gente).
_SAID = {"nequi": "Nequi", "daviplata": "Daviplata", "bank": "transferencia", "breb": "Bre-B"}
_ASKS = {"nequi": "Y Nequi no", "daviplata": "Y Daviplata no", "bank": "Y puedo trasferir", "breb": "Y por Bre-B no"}
_TYPO = {"nequi": "nekui", "daviplata": "davi plata"}

# Lo que se espera de un turno: nada en particular (""), que no le llegue el mensaje con los datos de pago (`NO_DETAILS`), que le
# lleguen en ese turno (`DETAILS`), que a esa altura ya le hayan llegado (`DETAILS_BY_NOW`) o que el chat pase al equipo (`REPORTED`).
NO_DETAILS, DETAILS, DETAILS_BY_NOW, REPORTED = "sin_datos", "datos", "datos_a_esta_altura", "pago_avisado"

EXACT_RULES = {
    "el_asesor_habla": "Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla.",
    "datos_cuando_los_necesita": "Los datos de pago le llegan cuando los pide o dice con qué medio paga.",
    "sin_datos_sin_pedirlos": "No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa.",
    "no_repite_el_bloque": "Los datos que ya tiene no se repiten si no los pide otra vez.",
    "sin_marcadores": "Nunca ve un marcador entre corchetes en lugar de un dato.",
    "pago_avisado_al_equipo": "Si dice que ya pagó, el chat pasa al equipo; si no, no pasa.",
    "no_repite_la_respuesta": "No le responde lo mismo dos veces seguidas.",
}
JUDGE_RULES = {
    "responde_lo_que_preguntan": (
        "Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde "
        "claramente si se puede o no. No pasa si ignora la pregunta o entiende lo contrario de lo que preguntó."
    ),
    "no_pide_lo_ya_dado": (
        "El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). Pedir "
        "un dato que el cliente todavía no ha dado sí pasa, aunque lo pida más de una vez."
    ),
    "no_dice_nada_falso_del_pago": (
        "El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un "
        "medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes "
        "aparece «[dato entregado por el motor]»."
    ),
    "explica_cuando_no_entienden": (
        "Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. No pasa si solo "
        "repite una frase suelta, lo ignora o cambia de tema."
    ),
    "coherente_con_los_datos": (
        "En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no "
        "dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). "
        "Pedirle otros datos en ese mismo mensaje sí pasa."
    ),
}
JUDGE = (
    "Eres auditor de calidad de un asesor de ventas por chat. Lee la conversación y busca fallas de estas reglas. Sé estricto pero "
    "justo: reporta una falla solo si puedes copiar la frase exacta del asesor que la muestra. Si una regla no aplica o se cumple, no "
    "la reportes.\n"
    "«[dato entregado por el motor]» es un dato de pago real (un número, una cuenta o un link) que el sistema le envió al cliente: en "
    "ese mensaje los datos sí le llegaron.\n\nREGLAS:\n"
    + "\n".join(f"- {name}: {text}" for name, text in JUDGE_RULES.items())
    + '\n\nDevuelve SOLO JSON: {"fallas": [{"regla": "<nombre de la regla>", "turno": <número del turno>, "cita": "<frase copiada tal '
    'cual del mensaje del asesor en ese turno>", "razon": "máximo 15 palabras"}]}. Sin fallas: {"fallas": []}.\n'
    "En «no_pide_lo_ya_dado» agrega «cita_cliente»: la frase copiada tal cual de un mensaje anterior del cliente donde ya había dado "
    "ese dato."
)
# Las reglas en las que el juez debe mostrar, además, lo que dijo antes el cliente (copiado tal cual de un turno anterior).
CUSTOMER_EVIDENCE = ("no_pide_lo_ya_dado",)
MIN_QUOTE_CHARS = 8


def _plain(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def judge_failures(verdict: dict, turns: list[dict]) -> tuple[dict[str, list[dict]], list[dict]]:
    """Las fallas que reportó el juez y que traen su prueba: por cada regla, dónde no pasa y por qué (lista vacía si pasa). Y las que
    se descartan por no traerla, para que queden a la vista.

    El juez se equivoca: marcó «pide lo ya dado» cuando el cliente no había dado el dato, y «no pasa» con una razón que decía que sí
    (13 nov 2026). Por eso una falla solo vale si su cita está, tal cual, en lo que dijo el asesor en ese turno (y, en las reglas de
    `CUSTOMER_EVIDENCE`, si la cita del cliente está en un mensaje suyo anterior). Sin veredicto del juez, ninguna regla se da por
    buena: todas cuentan como que no pasan, para mirarlas."""
    failures: dict[str, list[dict]] = {name: [] for name in JUDGE_RULES}
    reported = verdict.get("fallas")
    if not isinstance(reported, list):
        return {name: [{"turn": 0, "why": "el juez no dio veredicto"}] for name in JUDGE_RULES}, []
    by_number = {turn["turn"]: turn for turn in turns}
    discarded = []
    for item in reported:
        item = item if isinstance(item, dict) else {}
        rule, number, quote = str(item.get("regla") or ""), item.get("turno"), _plain(item.get("cita"))
        turn = by_number.get(number) if isinstance(number, int) else None
        valid = rule in JUDGE_RULES and turn is not None and len(quote) >= MIN_QUOTE_CHARS and quote in _plain(turn["reply"])
        if valid and rule in CUSTOMER_EVIDENCE:
            said = _plain(item.get("cita_cliente"))
            valid = len(said) >= 3 and any(said in _plain(earlier["message"]) for earlier in turns if earlier["turn"] < number)
        entry = {"turn": number if isinstance(number, int) else 0, "why": str(item.get("razon") or "")}
        if valid:
            failures[rule].append(entry)
        else:
            discarded.append({**entry, "rule": rule})
    return failures, discarded


# La segunda mirada: cada falla que señala el juez se revisa sola, con su regla y la conversación hasta ese turno. Un juez que lee
# toda la conversación de una vez se equivoca (marcó «no responde» ante un «Sí, aceptamos Nequi»); una pregunta enfocada acierta más.
CONFIRM = (
    "Revisas si una falla reportada en una conversación de ventas por chat es real. Lee la regla y la conversación hasta ese turno. "
    "Confirma solo si la última respuesta del asesor de verdad incumple esa regla; si la cumple o la regla no aplica, no la confirmes.\n"
    "«[dato entregado por el motor]» es un dato de pago real que el sistema le envió al cliente: en ese mensaje los datos sí le llegaron.\n"
    'Devuelve SOLO JSON: {"confirmada": true, "razon": "máximo 15 palabras"}'
)


def confirm_request(rule: str, turns: list[dict], failure: dict) -> str:
    """Lo que se le envía al segundo revisor: la regla, la conversación hasta el turno de la falla y lo que reportó el juez."""
    until = [turn for turn in turns if turn["turn"] <= failure["turn"]]
    transcript = "\n".join(f"[{turn['turn']}] Cliente: {turn['message']}\n[{turn['turn']}] Asesor: {turn['reply']}" for turn in until)
    return f"REGLA ({rule}): {JUDGE_RULES[rule]}\n\nCONVERSACIÓN HASTA ESE TURNO:\n{transcript}\n\nFALLA REPORTADA en el turno {failure['turn']}: {failure['why']}"


def keep_confirmed(failures: dict[str, list[dict]], turns: list[dict], confirm) -> tuple[dict[str, list[dict]], list[dict]]:
    """De las fallas que señaló el juez, las que confirma el segundo revisor (`confirm(rule, turns, failure)` → bool), y las que no.
    Las que no tienen turno (el juez no dio veredicto) se quedan: no hay qué revisar."""
    kept: dict[str, list[dict]] = {name: [] for name in failures}
    dropped = []
    for rule, items in failures.items():
        for failure in items:
            if not failure["turn"] or confirm(rule, turns, failure):
                kept[rule].append(failure)
            else:
                dropped.append({**failure, "rule": rule})
    return kept, dropped


def _methods(facts: dict) -> tuple[str, str]:
    """El medio con el que paga el cliente y otro por el que pregunta antes (o "" si el negocio tiene uno solo)."""
    available = [kind for kind in ("nequi", "daviplata", "breb", "bank") if facts["pagos_disponibles"].get(kind)]
    paid = available[0] if available else ""
    other = next((kind for kind in ("bank", "daviplata", "nequi", "breb") if kind in available and kind != paid), "")
    return paid, other


def conversations_for(facts: dict) -> list[tuple[str, list[dict]]]:
    """Las conversaciones del estándar para ese negocio: (nombre, turnos). Cada turno dice qué escribe el cliente y qué se espera."""
    offer = facts["oferta"][0]["name"] if facts["oferta"] else "lo que ofrecen"
    paid, other = _methods(facts)
    if not paid:
        return []
    said = _SAID[paid]
    production = [
        ("Hola", ""),
        (f"Me interesa {offer}, quiero empezar", NO_DETAILS),
        *([(_ASKS[other], NO_DETAILS)] if other else []),
        (_ASKS[paid], NO_DETAILS),
        ("Me llamo Juan Camilo y es una tienda de ropa", ""),
        (f"Te pago por {said}", DETAILS_BY_NOW),
        ("Mi teléfono es 3157778899", ""),
        ("Cuando lo haga que nesesito hacer", NO_DETAILS),
        ("Espérame un momento", NO_DETAILS),
        (f"Pero se me borró el {said} me lo envías de nuevo", DETAILS),
        ("Cómo así", NO_DETAILS),
        ("Ya voy a pagar", NO_DETAILS),
        ("ya te consigné", REPORTED),
    ]
    start = (f"Quiero {offer}", NO_DETAILS)
    short = [
        ("pide el medio con un error de escritura", [start, (f"Pásame el {_TYPO.get(paid, said)} porfa", DETAILS)]),
        ("pregunta a dónde consigna", [start, ("¿A qué número te consigno?", "")]),
        ("pregunta cómo paga", [start, ("cómo te pago", NO_DETAILS)]),
        ("pregunta si tienen un medio", [start, (f"¿Tienen {said}?", NO_DETAILS)]),
        *([("pide los datos de otro medio", [start, (f"listo, mándame los datos para pagar por {_SAID[other]}", DETAILS)])] if other else []),
    ]
    scripts = [("el chat de producción", production), *short]
    return [
        (name, [{"turn": number, "message": message, "kind": expect or "libre", "expect": expect} for number, (message, expect) in enumerate(script, start=1)])
        for name, script in scripts
    ]


def details_of(reply: str) -> str:
    """El mensaje con los datos de pago que va en esa respuesta (desde su primer renglón), o "" si no va: el dato dentro de una frase
    del asesor no cuenta. Dos mensajes iguales son los mismos datos, del mismo medio."""
    lines = [line.strip() for line in str(reply or "").splitlines()]
    if ENGINE_DATA not in str(reply or ""):
        return ""
    start = next((index for index, line in enumerate(lines) if line.startswith(_DETAILS_START)), None)
    if start is None:
        # Una plantilla propia del negocio, sin el encabezado de la plataforma: desde el renglón anterior al dato (el nombre del medio).
        start = next((max(index - 1, 0) for index, line in enumerate(lines) if line == ENGINE_DATA), None)
    return "" if start is None else "\n".join(line for line in lines[start:] if line)


def has_details(reply: str) -> bool:
    """Si en esa respuesta va el mensaje con los datos de pago (no solo el dato dentro de una frase del asesor)."""
    return bool(details_of(reply))


def exact_failures(turns: list[dict]) -> dict[str, list[dict]]:
    """Por cada regla exacta, los turnos donde no pasa: `{"turn", "why"}`. Sin fallas, la lista queda vacía."""
    failures: dict[str, list[dict]] = {name: [] for name in EXACT_RULES}

    def fail(rule: str, turn: dict, why: str) -> None:
        failures[rule].append({"turn": turn["turn"], "why": why})

    sent_before, previous, sent_details = False, "", set()
    for turn in turns:
        reply, expect = str(turn.get("reply") or ""), str(turn.get("expect") or "")
        details, delivered = details_of(reply), ENGINE_DATA in reply
        if delivered and reply.lstrip().startswith(_DETAILS_START):
            fail("el_asesor_habla", turn, "le llegó solo la plantilla, sin una palabra del asesor")
        if expect == DETAILS and not delivered:
            fail("datos_cuando_los_necesita", turn, "pidió los datos y no le llegaron")
        if expect == DETAILS_BY_NOW and not (delivered or sent_before):
            fail("datos_cuando_los_necesita", turn, "dijo con qué medio paga y todavía no tiene los datos")
        if expect == NO_DETAILS and details and details not in sent_details:
            fail("sin_datos_sin_pedirlos", turn, "le llegó la cuenta sin pedirla")
        if details in sent_details and expect != DETAILS:
            fail("no_repite_el_bloque", turn, "le llegaron otra vez los mismos datos sin pedirlos")
        if "[dato de pago]" in reply or _PLACEHOLDER.search(reply.replace(ENGINE_DATA, "")):
            fail("sin_marcadores", turn, "vio un marcador entre corchetes")
        if bool(turn.get("handoff")) != (expect == REPORTED):
            fail("pago_avisado_al_equipo", turn, "avisó que pagó y el chat no pasó al equipo" if expect == REPORTED else "el chat pasó al equipo sin motivo")
        if previous and reply.strip() == previous.strip():
            fail("no_repite_la_respuesta", turn, "repitió la respuesta anterior")
        sent_before, previous = sent_before or delivered, reply
        sent_details.update({details} - {""})
    return failures
