##### 🚨 DO NOT PATCH BEHAVIOR #####
# Este sistema es AI-FIRST.
#
# ❌ NO:
# - modificar respuestas manualmente
# - agregar lógica condicional de venta
# - parchear outputs
#
# ✅ SI:
# - mejorar contexto
# - mejorar instrucciones a la IA
#
# Si un test falla:
# -> corregir contexto o prompt
# -> NO tocar respuesta final
################################

##### MEMORY SALES USAGE #####
# Si el usuario mencionó dolor antes:
# - reutilizarlo explícitamente
# - convertirlo en presión
#
# Ejemplo:
# "eso que me dijiste de que estás perdiendo clientes..."
#
# La memoria debe empujar, no solo recordar.
################################

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class ConversationState:
    pain_detected: bool = False
    pain_timeline: list[str] | None = None
    urgency: str = ""
    last_intent: str = ""
    stage: str = ""
    objections: int = 0
    last_cta: str = ""


class MemoryRepositoryPort(Protocol):
    def save_message(self, *, tenant_slug: str, user_id: str, message_text: str, role: str = "user") -> None:
        ...

    def get_history(self, *, tenant_slug: str, user_id: str) -> list[dict[str, str]]:
        ...

    def set_last_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        ...

    def get_last_intent(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def set_detected_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        ...

    def get_detected_intent(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def set_payment_method(self, *, tenant_slug: str, user_id: str, method: str) -> None:
        ...

    def get_payment_method(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def set_payment_status(self, *, tenant_slug: str, user_id: str, status: str) -> None:
        ...

    def get_payment_status(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def set_last_pain(self, *, tenant_slug: str, user_id: str, pain: str) -> None:
        ...

    def get_last_pain(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def set_mode(self, *, tenant_slug: str, user_id: str, mode: str) -> None:
        ...

    def get_mode(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def set_stage(self, *, tenant_slug: str, user_id: str, stage: str) -> None:
        ...

    def get_stage(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def get_last_timestamp(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        ...

    def set_last_response(self, *, tenant_slug: str, user_id: str, response: str) -> None:
        ...

    def get_last_response(self, *, tenant_slug: str, user_id: str) -> str:
        ...

    def set_conversation_state(self, *, tenant_slug: str, user_id: str, state: ConversationState) -> None:
        ...

    def get_conversation_state(self, *, tenant_slug: str, user_id: str) -> ConversationState:
        ...

    def set_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        ...

    def get_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        ...

    def set_last_user_message_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        ...

    def get_last_user_message_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        ...

    def reset_conversation(self, *, tenant_slug: str, user_id: str) -> None:
        ...


class MemoryDomainService:
    """Dominio de memoria conversacional desacoplado de almacenamiento."""

    def __init__(self, repository: MemoryRepositoryPort) -> None:
        self._repository = repository

    @property
    def repository(self) -> MemoryRepositoryPort:
        return self._repository

    def save_message(self, *, tenant_slug: str, user_id: str, message_text: str, role: str = "user") -> None:
        self._repository.save_message(tenant_slug=tenant_slug, user_id=user_id, message_text=message_text, role=role)

    def get_history(self, *, tenant_slug: str, user_id: str) -> list[dict[str, str]]:
        return self._repository.get_history(tenant_slug=tenant_slug, user_id=user_id)

    def set_last_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        self._repository.set_last_intent(tenant_slug=tenant_slug, user_id=user_id, intent=intent)

    def get_last_intent(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_last_intent(tenant_slug=tenant_slug, user_id=user_id)

    def set_detected_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        self._repository.set_detected_intent(tenant_slug=tenant_slug, user_id=user_id, intent=intent)

    def get_detected_intent(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_detected_intent(tenant_slug=tenant_slug, user_id=user_id)

    def set_payment_method(self, *, tenant_slug: str, user_id: str, method: str) -> None:
        self._repository.set_payment_method(tenant_slug=tenant_slug, user_id=user_id, method=method)

    def get_payment_method(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_payment_method(tenant_slug=tenant_slug, user_id=user_id)

    def set_payment_status(self, *, tenant_slug: str, user_id: str, status: str) -> None:
        self._repository.set_payment_status(tenant_slug=tenant_slug, user_id=user_id, status=status)

    def get_payment_status(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_payment_status(tenant_slug=tenant_slug, user_id=user_id)

    def set_last_pain(self, *, tenant_slug: str, user_id: str, pain: str) -> None:
        self._repository.set_last_pain(tenant_slug=tenant_slug, user_id=user_id, pain=pain)

    def get_last_pain(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_last_pain(tenant_slug=tenant_slug, user_id=user_id)

    def build_sales_memory_usage(self, *, tenant_slug: str, user_id: str) -> str:
        pain = str(self.get_last_pain(tenant_slug=tenant_slug, user_id=user_id) or "").strip()
        state = self.get_conversation_state(tenant_slug=tenant_slug, user_id=user_id)
        timeline_raw = getattr(state, "pain_timeline", None)
        timeline = [str(item).strip() for item in (timeline_raw if isinstance(timeline_raw, list) else []) if str(item).strip()]

        merged: list[str] = []
        seen: set[str] = set()
        for item in [*timeline, pain]:
            normalized = str(item or "").strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)

        if len(merged) > 1:
            preview = ", ".join(merged[:3])
            suffix = "..." if len(merged) > 3 else ""
            return f"Has mencionado varias cosas: {preview}{suffix}"

        if pain:
            return f"eso que me dijiste de que {pain}"
        if merged:
            return f"eso que me dijiste de que {merged[0]}"
        return ""

    def set_mode(self, *, tenant_slug: str, user_id: str, mode: str) -> None:
        self._repository.set_mode(tenant_slug=tenant_slug, user_id=user_id, mode=mode)

    def get_mode(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_mode(tenant_slug=tenant_slug, user_id=user_id)

    def set_stage(self, *, tenant_slug: str, user_id: str, stage: str) -> None:
        self._repository.set_stage(tenant_slug=tenant_slug, user_id=user_id, stage=stage)

    def get_stage(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_stage(tenant_slug=tenant_slug, user_id=user_id)

    def get_last_timestamp(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        return self._repository.get_last_timestamp(tenant_slug=tenant_slug, user_id=user_id)

    def set_last_response(self, *, tenant_slug: str, user_id: str, response: str) -> None:
        self._repository.set_last_response(tenant_slug=tenant_slug, user_id=user_id, response=response)

    def get_last_response(self, *, tenant_slug: str, user_id: str) -> str:
        return self._repository.get_last_response(tenant_slug=tenant_slug, user_id=user_id)

    def set_conversation_state(self, *, tenant_slug: str, user_id: str, state: ConversationState) -> None:
        self._repository.set_conversation_state(tenant_slug=tenant_slug, user_id=user_id, state=state)

    def get_conversation_state(self, *, tenant_slug: str, user_id: str) -> ConversationState:
        return self._repository.get_conversation_state(tenant_slug=tenant_slug, user_id=user_id)

    def set_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        self._repository.set_initial_message_last_sent_at(
            tenant_slug=tenant_slug,
            user_id=user_id,
            sent_at=sent_at,
        )

    def get_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        return self._repository.get_initial_message_last_sent_at(tenant_slug=tenant_slug, user_id=user_id)

    def set_last_user_message_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        self._repository.set_last_user_message_at(
            tenant_slug=tenant_slug,
            user_id=user_id,
            sent_at=sent_at,
        )

    def get_last_user_message_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        return self._repository.get_last_user_message_at(tenant_slug=tenant_slug, user_id=user_id)

    def reset_conversation(self, *, tenant_slug: str, user_id: str) -> None:
        self._repository.reset_conversation(tenant_slug=tenant_slug, user_id=user_id)
