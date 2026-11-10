"""Arma el prompt de un mensaje por capas, de lo más fijo a lo más cambiante:

1. Plataforma: cómo vende el asistente y el formato de respuesta (igual para todos los negocios).
2. Manual del tipo de negocio (productos, planes, servicios o citas).
3. El negocio, lo que vende, cómo compra y recibe el cliente, cómo se paga y se cierra, sus políticas, sus indicaciones, su cliente, su
   estrategia de venta y sus preguntas frecuentes (cambian cuando publica).
4. Esta conversación: el momento y lo que se sabe del cliente (cambia en cada mensaje).

El orden permite que el proveedor reutilice de su caché el comienzo del prompt, que se repite en cada mensaje del mismo negocio, y deja
lo propio de este mensaje lo más cerca de la conversación, que viaja como mensajes (`history.py`). Cada capa se mide contra su
presupuesto (`budgets.py`). Al final, los datos de pago se reemplazan por su marcador: nunca llegan a la IA.
"""
from __future__ import annotations

from app.domain.business_config.payment_data import redact_payment_values
from app.infrastructure.ai.prompting import budgets, instructions
from app.infrastructure.ai.prompting.sections import (
    business,
    conversation,
    customer,
    delivery,
    guidance,
    knowledge,
    offer,
    payments,
    playbook,
    policies,
    strategy,
)
from app.infrastructure.ai.prompting.view import PromptView
from app.services.ai.output_contract import OUTPUT_CONTRACT
from app.utils.logger import logger


def render_sections(view: PromptView) -> dict[str, str]:
    """Cada capa del mensaje por nombre y en orden ("" si no aplica). Es lo que se mide contra los presupuestos."""
    return {
        "platform": f"{instructions.PLATFORM}\n\n{OUTPUT_CONTRACT}",
        "playbook": playbook.render(view),
        "business": business.render(view),
        "offer": offer.render(view),
        "delivery": delivery.render(view),
        "payments": payments.render(view),
        "policies": policies.render(view),
        "guidance": guidance.render(view),
        "customer": customer.render(view),
        "strategy": strategy.render(view),
        "knowledge": knowledge.build_knowledge_context(view.runtime, user_message=view.user_message),
        "conversation": conversation.render(view),
    }


def compose(view: PromptView) -> str:
    blocks = render_sections(view)
    for name, (size, budget) in budgets.over_budget({name: len(text) for name, text in blocks.items()}).items():
        logger.warning("prompt_section_over_budget", extra={"tenant": view.tenant, "section": name, "chars": size, "budget": budget})
    prompt = "\n\n".join(text for text in blocks.values() if text)
    if len(prompt) > budgets.TOTAL_BUDGET:
        logger.warning("prompt_over_budget", extra={"tenant": view.tenant, "chars": len(prompt), "budget": budgets.TOTAL_BUDGET})
    return redact_payment_values(prompt, view.runtime)
