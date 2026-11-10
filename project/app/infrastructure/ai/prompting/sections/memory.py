"""Lo que el asistente recuerda de esta conversación: estado, última intención y dolor, pago en curso y continuidad comercial.

La memoria comercial (`CommercialMemorySignal`, del selector de relevancia) reemplaza al recuento clásico cuando tiene peso; con peso
«light» o sin señal se usa el recuento clásico (contexto reciente, estado y dato previo).
"""
from __future__ import annotations

from app.infrastructure.ai.prompting import instructions
from app.infrastructure.ai.prompting.text import as_text
from app.infrastructure.ai.prompting.view import PromptView

CONTINUITY_HEADER = "CONTINUIDAD COMERCIAL:"


def recent_customer(view: PromptView) -> str:
    memory = view.memory
    entries = [
        ("Última intención detectada", as_text(memory.get("last_intent", ""))),
        ("Dolor detectado", as_text(memory.get("last_pain", ""))),
        ("Método de pago elegido", as_text(memory.get("metodo_pago_elegido", ""))),
        ("Estado de pago recordado", as_text(memory.get("estado_pago", ""))),
    ]
    lines = [f"- {label}: {value}" for label, value in entries if value]
    last_reply = as_text(memory.get("last_ai_response") or memory.get("last_response"))
    if last_reply:
        lines += [f"- Última respuesta enviada: {last_reply}", instructions.DONT_REPEAT_LAST_REPLY]
    return "\n".join(["Contexto reciente del cliente:", *lines]) if lines else ""


def conversation_state(view: PromptView) -> str:
    memory = view.memory
    summary = memory.get("history_summary", "")
    price_anchor = memory.get("price_anchor", "")
    legend = instructions.CONVERSATION_STATE_LEGEND
    if price_anchor:
        # Sin recortar: este bloque deja líneas en blanco a su alrededor dentro del prompt.
        return f"\nEstado de la conversación: {view.state_label}\n{legend}\nEste cliente ya conoce el precio: {price_anchor}.\nContexto previo: {summary}\n"
    return f"Estado de la conversación: {view.state_label}\n    Contexto previo: {summary}\n{legend}"


def sales_memory_hint(view: PromptView) -> str:
    hint = as_text(view.memory.get("sales_memory_hint", ""))
    return instructions.RESUME_SALES_HINT.format(hint=hint) if hint else ""


def commercial_signal_weight(view: PromptView) -> str:
    signal = view.runtime.get("commercial_memory_signal")
    return str(getattr(signal, "context_weight", "light") or "light").strip().lower()


def commercial_memory(view: PromptView) -> str:
    """La continuidad comercial en palabras para el asistente; "" sin señal o con peso «light»."""
    signal = view.runtime.get("commercial_memory_signal")
    if signal is None or commercial_signal_weight(view) == "light":
        return ""
    parts = (getattr(signal, name, "") for name in ("continuity_brief", "commercial_anchor_active", "episodic_hook"))
    return "\n".join(text for part in parts if (text := str(part or "").strip()))


def operational(view: PromptView) -> str:
    """El proceso en curso (por ejemplo, un pago) y su regla, si hay uno activo."""
    anchor = str(view.memory.get("operational_anchor") or "").strip()
    rule = str(view.memory.get("operational_rule") or "").strip()
    if not anchor:
        return ""
    return f"{anchor}\n{rule}" if rule else anchor


def payment(view: PromptView) -> str:
    """El pago que ya eligió o reportó el cliente, para no reiniciarlo."""
    method = as_text(view.memory.get("metodo_pago_elegido", "")) or "none"
    status = as_text(view.memory.get("estado_pago", "")) or "none"
    if method == "none" and status == "none":
        return ""
    return instructions.PAYMENT_MEMORY.format(metodo_pago_elegido=method, estado_pago=status)
