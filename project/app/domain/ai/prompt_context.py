from __future__ import annotations

# ================================
# AI-FIRST MODULE
# -------------------------------
# Este modulo NO usa logica por palabras.
# Este modulo NO reescribe respuestas.
# La IA es la unica responsable del contenido.
# ================================
def _recent_messages(history: list) -> list[str]:
    items: list[str] = []
    for entry in history[-8:]:
        if isinstance(entry, dict):
            text = str(entry.get("text") or entry.get("message_text") or "").strip()
        else:
            text = str(entry or "").strip()
        if text:
            items.append(text)
    return items


def _history_summary(*, explicit_summary: str, recent_messages: list[str]) -> str:
    summary = str(explicit_summary or "").strip()
    if summary:
        return summary
    if not recent_messages:
        return ""
    return " | ".join(recent_messages[-3:])


def build_prompt_context(*, user_message: str, yaml_config: dict | None, memory: dict | None = None) -> dict:
    flow_context = (yaml_config or {}).get("flow_context") if isinstance(yaml_config, dict) else {}
    conversation_history = (yaml_config or {}).get("conversation_history") if isinstance(yaml_config, dict) else []
    if not isinstance(conversation_history, list):
        conversation_history = []

    runtime_context = flow_context.get("context") if isinstance(flow_context, dict) and isinstance(flow_context.get("context"), dict) else {}
    commercial_memory = runtime_context.get("commercial_memory") if isinstance(runtime_context.get("commercial_memory"), dict) else {}
    memory_context = memory if isinstance(memory, dict) else {}

    last_pain = str(memory_context.get("last_pain") or (yaml_config or {}).get("active_pain") or "").strip()
    stage_from_memory = str(memory_context.get("stage") or "").strip().lower()
    recent_messages = _recent_messages(conversation_history)
    history_summary = _history_summary(
        explicit_summary=str(memory_context.get("history_summary") or "").strip(),
        recent_messages=recent_messages,
    )
    force_initial_context = bool((yaml_config or {}).get("force_initial_context"))
    first_message_with_user_intent = bool((yaml_config or {}).get("first_message_with_user_intent"))

    context = {
        "last_intent": str(
            memory_context.get("last_intent")
            or (yaml_config or {}).get("last_intent")
            or ""
        ).strip().lower(),
        "last_pain": last_pain,
        "stage": stage_from_memory,
        "history_summary": history_summary,
        "recent_messages": recent_messages,
        "force_initial_context": force_initial_context,
        "first_message_with_user_intent": first_message_with_user_intent,
    }

    return context
