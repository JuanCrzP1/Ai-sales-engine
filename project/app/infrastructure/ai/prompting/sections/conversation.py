"""«ESTA CONVERSACIÓN»: el momento de la conversación y lo que ya se sabe del cliente. Va al final, lo más cerca del mensaje actual.

Solo la regla del momento (no la lista de todos los estados), y los hechos que importan para no repetir ni reiniciar: qué necesita,
si ya eligió cómo pagar o dijo que pagó (y el mensaje del negocio para después de la compra), el proceso en curso y la continuidad comercial. La conversación misma (los últimos mensajes)
no va aquí: viaja como mensajes (`history.py`).
"""
from __future__ import annotations

from app.domain.business_config.payment_catalog import method_kind
from app.infrastructure.ai.prompting import instructions
from app.infrastructure.ai.prompting.text import as_dict, as_text, bullets, one_line, section
from app.infrastructure.ai.prompting.view import PromptView

_METHODS = {"nequi": "Nequi", "daviplata": "Daviplata", "bank": "transferencia bancaria", "breb": "Bre-B", "link": "link de pago"}


def _method_name(method: str) -> str:
    """Cómo se nombra el medio que eligió: los de siempre como antes; los demás, por su nombre en el catálogo."""
    if method in _METHODS:
        return _METHODS[method]
    kind = method_kind(method.split(":", 1)[0])
    return kind.name if kind is not None and not kind.custom else method


def _moment(view: PromptView) -> str:
    if view.state == "warm":
        return instructions.STATE_RULES["resumed"]
    if view.state == "cold":
        return instructions.STATE_RULES["restarted"]
    if view.state == "new" and not view.prior_ai_response:
        return instructions.STATE_RULES["start"]
    return instructions.STATE_RULES["ongoing"]


def commercial_memory(view: PromptView) -> list[str]:
    """La continuidad comercial que elige el selector de memoria; nada si su peso es «light» o no hay señal."""
    signal = view.runtime.get("commercial_memory_signal")
    if signal is None or str(getattr(signal, "context_weight", "light") or "light").strip().lower() == "light":
        return []
    return [text for name in ("continuity_brief", "commercial_anchor_active", "episodic_hook") if (text := one_line(getattr(signal, name, "")))]


def render(view: PromptView) -> str:
    memory = view.memory
    facts = []
    pain = one_line(memory.get("last_pain"))
    if pain:
        facts.append(f"Lo que necesita: {pain}")
    method = as_text(memory.get("metodo_pago_elegido")).lower()
    status = as_text(memory.get("estado_pago")).lower()
    if status == "reportado":
        facts.append(instructions.PAYMENT_REPORTED)
        after_sale = one_line(as_dict(view.config.get("messages")).get("after_sale"))
        if after_sale:
            facts.append(instructions.AFTER_SALE.format(message=after_sale))
    elif method:
        facts.append(instructions.PAYMENT_CHOSEN.format(method=_method_name(method)))
    anchor, rule = one_line(memory.get("operational_anchor")), one_line(memory.get("operational_rule"))
    if anchor:
        facts.append(f"{anchor} {rule}".strip())
    price_anchor = one_line(memory.get("price_anchor"))
    if price_anchor:
        facts.append(f"Ya conoce el precio: {price_anchor}")
    hint = one_line(memory.get("sales_memory_hint"))
    if hint:
        facts.append(f"Dato que contó antes: {hint}")
    facts += commercial_memory(view)
    return section(instructions.CONVERSATION_HEADER, [_moment(view), *bullets(facts)])
