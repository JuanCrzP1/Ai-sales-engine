"""Arma el prompt de un mensaje: elige qué bloques van, en qué orden y bajo qué encabezado.

El orden depende de la memoria comercial de la conversación (`memory.commercial_signal_weight`):

- fuerte: la continuidad comercial va al final, después de los precios, lo más cerca posible del mensaje del cliente;
- moderada: reemplaza al recuento clásico de la memoria, antes de los precios;
- sin señal o ligera: el recuento clásico (contexto reciente, estado de la conversación y dato previo).

Cada bloque se mide contra su presupuesto (`budgets.py`). Al final, los datos de pago se reemplazan por su marcador: nunca llegan a la
IA, ni desde la configuración ni desde el historial.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.business_config.payment_data import redact_payment_values
from app.infrastructure.ai.prompting import budgets, instructions
from app.infrastructure.ai.prompting.sections import capabilities, identity, knowledge, memory, post_payment, pricing, profile, sales, style
from app.infrastructure.ai.prompting.view import PromptView
from app.utils.logger import logger

RULES_HEADER = "REGLAS OPERATIVAS:"
BEHAVIOR_HEADER = "COMPORTAMIENTO COMERCIAL:"
PRICING_HEADER = "PRICING:"


@dataclass(frozen=True)
class Group:
    """Un encabezado y sus partes, una por línea. Una parte vacía deja su línea en blanco."""

    header: str
    parts: tuple[str, ...]

    def render(self) -> str:
        return "\n".join((self.header, *self.parts))


def _groups(*groups: Group) -> str:
    return "\n\n".join(group.render() for group in groups)


def render_sections(view: PromptView) -> dict[str, str]:
    """Cada bloque del mensaje por nombre, ya resuelto ("" si no aplica). Es lo que se mide contra los presupuestos."""
    presents = view.presents_business
    commercial = memory.commercial_memory(view)
    return {
        "identity": identity.render(view),
        "rules": instructions.GROUNDING,
        "business_model": capabilities.business_model_line(view),
        "catalog_steering": capabilities.catalog_steering(view),
        "capabilities": capabilities.render(view),
        "profile": profile.build_business_profile_context(view.runtime, include_facts=presents, query=view.relevance_query),
        "knowledge": knowledge.build_knowledge_context(view.runtime, user_message=view.user_message),
        "operational": memory.operational(view),
        "behavior": instructions.COMMERCIAL_BEHAVIOR,
        "sales": sales.render(view) if presents else "",
        "continuity_rule": instructions.CONTINUITY_RULE if not presents else "",
        "commercial": commercial,
        "recent": memory.recent_customer(view) if not commercial else "",
        "state": memory.conversation_state(view) if not commercial else "",
        "hint": memory.sales_memory_hint(view) if not commercial else "",
        "style": style.render(view),
        "payment": memory.payment(view),
        "pricing": pricing.render(view),
        "post_payment": post_payment.render(view),
    }


def _sizes(blocks: dict[str, str]) -> dict[str, int]:
    """Los bloques agrupados como los presupuesta `budgets.py`."""
    size = {name: len(text) for name, text in blocks.items()}
    return {
        **{name: size[name] for name in ("identity", "rules", "profile", "knowledge", "behavior", "sales", "style", "pricing", "post_payment")},
        "capabilities": size["business_model"] + size["catalog_steering"] + size["capabilities"],
        "memory": size["operational"] + size["recent"] + size["state"] + size["hint"] + size["payment"],
        "continuity": size["commercial"],
    }


def compose(view: PromptView) -> str:
    presents = view.presents_business
    if not presents:
        logger.info({"event": "backend_prompt_steering", "type": "intro_suppression", "tenant": view.tenant, "user_id": view.user_id})
    blocks = render_sections(view)
    exceeded = budgets.over_budget(_sizes(blocks))
    for name, (size, budget) in exceeded.items():
        logger.warning("prompt_section_over_budget", extra={"tenant": view.tenant, "section": name, "chars": size, "budget": budget})

    context = _groups(
        Group(identity.HEADER, (blocks["identity"], "")),
        Group(RULES_HEADER, (blocks["rules"],)),
        Group(capabilities.HEADER, (blocks["business_model"], blocks["catalog_steering"], blocks["capabilities"])),
    ).strip()
    head = "\n\n".join(block for block in (context, blocks["profile"], blocks["knowledge"]) if block)

    weight = memory.commercial_signal_weight(view)
    behavior_start = (blocks["operational"], blocks["behavior"], blocks["sales"], blocks["continuity_rule"])
    behavior_end = (blocks["style"], blocks["payment"])
    continuity = ""
    if blocks["commercial"] and weight == "strong":
        recount: tuple[str, ...] = ()
        continuity = blocks["commercial"]
    elif blocks["commercial"]:
        recount = (blocks["commercial"],)
    else:
        recount = (blocks["recent"], blocks["state"], blocks["hint"])

    groups = [Group(BEHAVIOR_HEADER, (*behavior_start, *recount, *behavior_end)), Group(PRICING_HEADER, (blocks["pricing"], blocks["post_payment"]))]
    if continuity:
        groups.append(Group(memory.CONTINUITY_HEADER, (continuity,)))
    prompt = f"{head}\n\n{_groups(*groups)}".strip()
    total = len(prompt)
    if total > budgets.TOTAL_BUDGET:
        logger.warning("prompt_over_budget", extra={"tenant": view.tenant, "chars": total, "budget": budgets.TOTAL_BUDGET})
    return redact_payment_values(prompt, view.runtime)
