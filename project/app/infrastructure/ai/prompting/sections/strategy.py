"""«ESTRATEGIA DE VENTA DEL NEGOCIO»: cómo quiere el negocio que avance la venta. El orden de la conversación y lo que no debe hacer, cómo
atender una pregunta, qué averiguar, cómo presentar las opciones y cómo cerrar (señales de compra, pasos y reglas).

Es la estrategia avanzada del panel; si el negocio no la escribió, esta capa no va y manda el manual de su tipo de negocio. La IA guía al
cliente hacia los siguientes pasos de la venta; no dice que ya están hechos (enviar la orden a cocina o activar un servicio los hace el
equipo). Si todo cabe en `STRATEGY_PROMPT_MAX_CHARS`, va todo; si no, lo más relacionado con lo que dice el cliente (`relevance.py`).
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import STRATEGY_PROMPT_MAX_CHARS
from app.infrastructure.ai.prompting import relevance
from app.infrastructure.ai.prompting.text import as_dict, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView
from app.infrastructure.ai.prompting.vocabulary import FORBIDDEN, STEPS, quoted, said_all

HEADER = "ESTRATEGIA DE VENTA DEL NEGOCIO"
_EXPLAIN_FIRST = {
    True: "Si pregunta algo, primero respóndele con claridad.",
    False: "Si pide información, responde breve y conéctala con lo que necesita para avanzar.",
}
SELL_AFTER = "Después de aclarar su duda, invítalo a avanzar."
OFFER_FIT = "Antes de llevarlo a comprar, confirma que la opción le sirve para lo que necesita."
GUIDED = "Guíalo paso a paso por el proceso."
ATTENTION_RULES = "Reglas de atención del negocio:"
CLOSING_RULES = "Reglas de cierre del negocio:"
Entry = tuple[str | None, str]


def _plain(lines: list[str]) -> list[Entry]:
    """Líneas sueltas (sin grupo) como entradas de la capa."""
    return [(None, line) for line in lines if line]


def _flow(sales: dict) -> list[str]:
    flow, progression = as_dict(sales.get("conversation_flow")), as_dict(sales.get("progression_rules"))
    rules = as_dict(flow.get("rules"))
    steps, required = said_all(texts(flow.get("steps")), STEPS), said_all(texts(progression.get("required_flow")), STEPS)
    order = steps or required
    forbidden = said_all(texts(progression.get("forbid")), FORBIDDEN)
    return [
        sentence(f"Orden de la conversación: {' → '.join(order)}") + (" No te saltes pasos." if rules.get("no_skip_steps") is True else "") if order else "",
        sentence(f"Pasos que no pueden faltar: {' → '.join(required)}") if steps and required and required != steps else "",
        GUIDED if rules.get("guided_process") is True else "",
        sentence(f"No hagas esto: {'; '.join(forbidden)}") if forbidden else "",
    ]


def _attention(sales: dict) -> list[Entry]:
    support = as_dict(sales.get("support"))
    handling = as_dict(support.get("info_handling"))
    rules = texts(support.get("hard_rules"))
    return _plain([
        _EXPLAIN_FIRST.get(handling.get("explain_first"), "") if isinstance(handling.get("explain_first"), bool) else "",
        SELL_AFTER if handling.get("sell_after") is True else "",
        OFFER_FIT if as_dict(sales.get("qualification")).get("detect_offer_fit") is True else "",
    ]) + [(ATTENTION_RULES, rule) for rule in rules]


def _discovery_and_presentation(sales: dict) -> list[str]:
    objectives = texts(as_dict(sales.get("discovery")).get("objectives"))
    presentation = as_dict(as_dict(sales.get("offer")).get("strategy"))
    single, several = texts(presentation.get("single")), texts(presentation.get("multi"))
    return [
        sentence(f"Lo que debes averiguar del cliente: {'; '.join(objectives)}") if objectives else "",
        sentence(f"Si hay una sola opción para él: {'; '.join(single)}") if single else "",
        sentence(f"Si hay varias opciones: {'; '.join(several)}") if several else "",
    ]


def _closing(sales: dict) -> list[Entry]:
    closing = as_dict(sales.get("closing"))
    signals, high_intent = texts(closing.get("triggers")), texts(as_dict(closing.get("actions")).get("high_intent"))
    next_steps, commitments, rules = texts(closing.get("next_steps")), texts(closing.get("micro_commitments")), texts(closing.get("hard_rules"))
    return _plain([
        sentence(f"Señales de que quiere comprar: {quoted(signals)}") if signals else "",
        sentence(f"Si muestra mucha intención de compra: {', '.join(high_intent)}") if high_intent else "",
        sentence(f"Siguientes pasos de la venta (guía al cliente hacia ellos; no digas que ya están hechos): {', '.join(next_steps)}") if next_steps else "",
        sentence(f"Compromisos pequeños para avanzar: {'; '.join(commitments)}") if commitments else "",
    ]) + [(CLOSING_RULES, rule) for rule in rules]


def render(view: PromptView) -> str:
    sales = view.sales
    entries = [*_plain(_flow(sales)), *_attention(sales), *_plain(_discovery_and_presentation(sales)), *_closing(sales)]
    return section(HEADER, relevance.grouped_lines(entries, query=view.relevance_query, max_chars=STRATEGY_PROMPT_MAX_CHARS))
