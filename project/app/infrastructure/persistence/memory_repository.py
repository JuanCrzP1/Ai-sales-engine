##### 🚨 NON-PERSISTENT MEMORY #####
# Esta memoria NO es persistente.
#
# ❌ Problemas:
# - se pierde en reinicios
# - no escala en multi-tenant real
#
# ⚠️ Esto es temporal.
# Debe migrarse a base de datos.
########################################

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.conversation.memory import ConversationState
from app.utils.logger import logger


class MemoryRepository:
    """In-memory repository; interface lista para persistencia SQL."""

    def __init__(self) -> None:
        self._messages_by_user: dict[tuple[str, str], list[dict[str, object] | str]] = {}
        self._last_intent_by_user: dict[tuple[str, str], str] = {}
        self._detected_intent_by_user: dict[tuple[str, str], str] = {}
        self._last_pain_by_user: dict[tuple[str, str], str] = {}
        self._payment_method_by_user: dict[tuple[str, str], str] = {}
        self._payment_status_by_user: dict[tuple[str, str], str] = {}
        self._mode_by_user: dict[tuple[str, str], str] = {}
        self._stage_by_user: dict[tuple[str, str], str] = {}
        self._last_user_message_by_user: dict[tuple[str, str], str] = {}
        self._last_response_by_user: dict[tuple[str, str], str] = {}
        self._last_ai_response_by_user: dict[tuple[str, str], str] = {}
        self._conversation_state_by_user: dict[tuple[str, str], dict[str, object]] = {}
        self._initial_message_last_sent_by_user: dict[tuple[str, str], datetime] = {}
        self._last_user_message_at_by_user: dict[tuple[str, str], datetime] = {}

    @staticmethod
    def _key(*, tenant_slug: str, user_id: str) -> tuple[str, str] | None:
        normalized_slug = str(tenant_slug or "").strip().lower()
        normalized_user = str(user_id or "").strip().lower()
        if not normalized_slug or not normalized_user:
            return None
        return normalized_slug, normalized_user

    def reset_conversation(self, *, tenant_slug: str, user_id: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return

        self._messages_by_user.pop(key, None)
        self._last_intent_by_user.pop(key, None)
        self._detected_intent_by_user.pop(key, None)
        self._last_pain_by_user.pop(key, None)
        self._payment_method_by_user.pop(key, None)
        self._payment_status_by_user.pop(key, None)
        self._mode_by_user.pop(key, None)
        self._stage_by_user.pop(key, None)
        self._last_user_message_by_user.pop(key, None)
        self._last_response_by_user.pop(key, None)
        self._last_ai_response_by_user.pop(key, None)
        self._conversation_state_by_user.pop(key, None)
        self._initial_message_last_sent_by_user.pop(key, None)
        self._last_user_message_at_by_user.pop(key, None)

    def save_message(self, *, tenant_slug: str, user_id: str, message_text: str) -> None:
        # Hoy: in-memory. Manana: persistencia en DB por tenant/user.
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        text = str(message_text or "").strip()
        if not text:
            return
        history = self._messages_by_user.get(key, [])
        history.append({"text": text, "timestamp": datetime.now(timezone.utc)})
        self._messages_by_user[key] = history[-20:]
        self._last_user_message_by_user[key] = text

    def get_history(self, *, tenant_slug: str, user_id: str) -> list[dict[str, str]]:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return []
        items: list[dict[str, str]] = []
        for entry in self._messages_by_user.get(key, []):
            if isinstance(entry, dict):
                text = str(entry.get("text") or "").strip()
            else:
                text = str(entry or "").strip()
            if text:
                items.append({"text": text})
        return items

    def set_last_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        self._last_intent_by_user[key] = str(intent or "").strip().lower()

    def get_last_intent(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._last_intent_by_user.get(key) or "")

    def set_detected_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        normalized = str(intent or "").strip().lower()
        if normalized:
            self._detected_intent_by_user[key] = normalized
        else:
            self._detected_intent_by_user.pop(key, None)

    def get_detected_intent(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._detected_intent_by_user.get(key) or "")

    def set_payment_method(self, *, tenant_slug: str, user_id: str, method: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        normalized = str(method or "").strip().lower()
        if normalized:
            self._payment_method_by_user[key] = normalized
        else:
            self._payment_method_by_user.pop(key, None)

    def get_payment_method(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._payment_method_by_user.get(key) or "")

    def set_payment_status(self, *, tenant_slug: str, user_id: str, status: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        normalized = str(status or "").strip().lower()
        if normalized:
            self._payment_status_by_user[key] = normalized
        else:
            self._payment_status_by_user.pop(key, None)

    def get_payment_status(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._payment_status_by_user.get(key) or "")

    def set_last_pain(self, *, tenant_slug: str, user_id: str, pain: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        normalized = str(pain or "").strip().lower()
        if normalized:
            self._last_pain_by_user[key] = normalized

    def get_last_pain(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._last_pain_by_user.get(key) or "")

    def set_mode(self, *, tenant_slug: str, user_id: str, mode: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        normalized = str(mode or "").strip().lower()
        if normalized:
            self._mode_by_user[key] = normalized
        else:
            self._mode_by_user.pop(key, None)

    def get_mode(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._mode_by_user.get(key) or "")

    def set_stage(self, *, tenant_slug: str, user_id: str, stage: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        self._stage_by_user[key] = str(stage or "").strip().lower()

    def get_stage(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._stage_by_user.get(key) or "")

    def get_last_timestamp(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return None
        history = self._messages_by_user.get(key, [])
        if not history:
            return None
        last_entry = history[-1]
        if isinstance(last_entry, dict):
            timestamp = last_entry.get("timestamp")
            if isinstance(timestamp, datetime):
                return timestamp
        return None

    def set_last_response(self, *, tenant_slug: str, user_id: str, response: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        text = str(response or "").strip()
        if not text:
            return
        self._last_response_by_user[key] = text
        self._last_ai_response_by_user[key] = text

    def get_last_response(self, *, tenant_slug: str, user_id: str) -> str:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ""
        return str(self._last_response_by_user.get(key) or "")

    def set_conversation_state(self, *, tenant_slug: str, user_id: str, state: ConversationState) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        timeline = getattr(state, "pain_timeline", None)
        timeline_list = timeline if isinstance(timeline, list) else []
        normalized_timeline = [str(item).strip() for item in timeline_list if str(item).strip()]

        self._conversation_state_by_user[key] = {
            "pain_detected": bool(getattr(state, "pain_detected", False)),
            "pain_timeline": normalized_timeline[-20:],
            "urgency": str(getattr(state, "urgency", "") or "").strip().lower(),
            "last_intent": str(getattr(state, "last_intent", "") or "").strip().lower(),
            "stage": str(getattr(state, "stage", "") or "").strip().lower(),
            "objections": max(0, int(getattr(state, "objections", 0) or 0)),
            "last_cta": str(getattr(state, "last_cta", "") or "").strip(),
        }

    def get_conversation_state(self, *, tenant_slug: str, user_id: str) -> ConversationState:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return ConversationState()
        raw = self._conversation_state_by_user.get(key, {})
        timeline = raw.get("pain_timeline") if isinstance(raw.get("pain_timeline"), list) else []
        return ConversationState(
            pain_detected=bool(raw.get("pain_detected", False)),
            pain_timeline=[str(item).strip() for item in timeline if str(item).strip()],
            urgency=str(raw.get("urgency") or "").strip().lower(),
            last_intent=str(raw.get("last_intent") or "").strip().lower(),
            stage=str(raw.get("stage") or "").strip().lower(),
            objections=max(0, int(raw.get("objections") or 0)),
            last_cta=str(raw.get("last_cta") or "").strip(),
        )

    def set_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        if not isinstance(sent_at, datetime):
            return
        self._initial_message_last_sent_by_user[key] = sent_at

    def get_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return None
        value = self._initial_message_last_sent_by_user.get(key)
        if isinstance(value, datetime):
            return value
        return None

    def set_last_user_message_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        if not isinstance(sent_at, datetime):
            return
        logger.info(
            {
                "event": "saving_last_user_message_at",
                "user_id": key[1],
                "tenant": key[0],
                "timestamp": sent_at,
            }
        )
        self._last_user_message_at_by_user[key] = sent_at

    def get_last_user_message_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return None
        value = self._last_user_message_at_by_user.get(key)
        logger.info(
            {
                "event": "loading_last_user_message_at",
                "user_id": key[1],
                "tenant": key[0],
                "value": value,
            }
        )
        if isinstance(value, datetime):
            return value
        return None

    # ------------------------------------------------------------------
    # ConversationMemoryRepository interface (forward-compatible)
    # ------------------------------------------------------------------

    def get_memory(self, tenant_slug: str, user_id: str) -> dict:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return {}
        return {
            "last_user_message_at": self._last_user_message_at_by_user.get(key),
            "initial_message_last_sent_at": self._initial_message_last_sent_by_user.get(key),
            "last_intent": self._last_intent_by_user.get(key),
            "intent_detectado": self._detected_intent_by_user.get(key),
            "metodo_pago_elegido": self._payment_method_by_user.get(key),
            "estado_pago": self._payment_status_by_user.get(key),
            "last_user_message": self._last_user_message_by_user.get(key),
            "last_ai_response": self._last_ai_response_by_user.get(key),
        }

    def update_last_user_message_at(
        self, tenant_slug: str, user_id: str, timestamp: datetime
    ) -> None:
        self.set_last_user_message_at(tenant_slug=tenant_slug, user_id=user_id, sent_at=timestamp)

    def update_initial_message_last_sent_at(
        self, tenant_slug: str, user_id: str, timestamp: datetime
    ) -> None:
        self.set_initial_message_last_sent_at(tenant_slug=tenant_slug, user_id=user_id, sent_at=timestamp)


class SQLMemoryRepository(MemoryRepository):
    """SQL-ready placeholder preserving MemoryRepository contract."""

    pass
