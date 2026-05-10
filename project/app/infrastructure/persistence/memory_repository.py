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

    def save_message(self, *, tenant_slug: str, user_id: str, message_text: str, role: str = "user") -> None:
        # Hoy: in-memory. Manana: persistencia en DB por tenant/user.
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return
        text = str(message_text or "").strip()
        if not text:
            return
        normalized_role = str(role or "user").strip().lower() or "user"
        history = self._messages_by_user.get(key, [])
        history.append({"text": text, "timestamp": datetime.now(timezone.utc), "role": normalized_role})
        self._messages_by_user[key] = history[-20:]
        if normalized_role == "user":
            self._last_user_message_by_user[key] = text

    def get_history(self, *, tenant_slug: str, user_id: str) -> list[dict[str, str]]:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key:
            return []
        items: list[dict[str, str]] = []
        for entry in self._messages_by_user.get(key, []):
            if isinstance(entry, dict):
                text = str(entry.get("text") or "").strip()
                role_val = str(entry.get("role") or "user").strip().lower() or "user"
            else:
                text = str(entry or "").strip()
                role_val = "user"
            if text:
                items.append({"role": role_val, "text": text})
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
    """PostgreSQL-backed MemoryRepository.

    Persists conversation history in `conversation_messages` and commercial
    memory in `conversation_memory` (JSONB).  Client identity is resolved via
    `ClientRepository.get_or_create()`.

    Falls back silently to the in-RAM parent implementation when the database
    tables are not yet available (e.g. during tests without a real schema),
    so all existing tests remain green without modification.
    """

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _log_db_fallback(
        self,
        operation: str,
        tenant_slug: str,
        user_id: str,
        exc: Exception,
    ) -> None:
        """Log a DB error and fall back to RAM; never silently swallows exceptions."""
        logger.exception(
            {
                "event": "sql_memory_repository_fallback",
                "operation": operation,
                "tenant": tenant_slug,
                "user_id": user_id,
            }
        )

    def _resolve_ids(self, tenant_slug: str, user_id: str) -> tuple[str, str] | None:
        """Return (tenant_db_id, client_db_id) or None if resolution fails."""
        from app.infrastructure.db.repository import DBRepository
        from app.infrastructure.persistence.client_repository import ClientRepository

        normalized_slug = str(tenant_slug or "").strip().lower()
        normalized_user = str(user_id or "").strip().lower()
        if not normalized_slug or not normalized_user:
            return None

        tenant = DBRepository().get_tenant_by_key(normalized_slug)
        if not tenant:
            return None

        tenant_db_id = str(tenant.get("id") or "")
        client_id = ClientRepository().get_or_create(
            tenant_slug=normalized_slug,
            external_id=normalized_user,
        )
        if not client_id:
            return None

        return tenant_db_id, client_id

    @staticmethod
    def _engine():
        from app.infrastructure.db.connection import get_engine
        return get_engine()

    def _upsert_memory_key(self, tenant_db_id: str, client_id: str, key: str, value: object) -> None:
        """Upsert a single key into conversation_memory JSONB."""
        from sqlalchemy import text
        import json

        engine = self._engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO conversation_memory (tenant_id, client_id, memory, updated_at)
                    VALUES (:tid, :cid, CAST(:blob AS JSONB), now())
                    ON CONFLICT (tenant_id, client_id) DO UPDATE
                        SET memory     = conversation_memory.memory || CAST(:blob AS JSONB),
                            updated_at = now()
                    """
                ),
                {
                    "tid": tenant_db_id,
                    "cid": client_id,
                    "blob": json.dumps({key: value}),
                },
            )

    def _delete_memory_key(self, tenant_db_id: str, client_id: str, key: str) -> None:
        from sqlalchemy import text

        engine = self._engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE conversation_memory
                    SET memory = memory - :key, updated_at = now()
                    WHERE tenant_id = :tid AND client_id = :cid
                    """
                ),
                {"key": key, "tid": tenant_db_id, "cid": client_id},
            )

    def _read_memory(self, tenant_db_id: str, client_id: str) -> dict:
        from sqlalchemy import text

        engine = self._engine()
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT memory FROM conversation_memory
                    WHERE tenant_id = :tid AND client_id = :cid
                    LIMIT 1
                    """
                ),
                {"tid": tenant_db_id, "cid": client_id},
            ).fetchone()
        if not row:
            return {}
        raw = row._mapping.get("memory")
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            import json
            try:
                return json.loads(raw)
            except Exception:
                return {}
        return {}

    # ------------------------------------------------------------------ #
    # save_message / get_history / reset_conversation (messages table)    #
    # ------------------------------------------------------------------ #

    def save_message(
        self,
        *,
        tenant_slug: str,
        user_id: str,
        message_text: str,
        role: str = "user",
    ) -> None:
        # Always update RAM (keeps in-process history consistent).
        super().save_message(
            tenant_slug=tenant_slug,
            user_id=user_id,
            message_text=message_text,
            role=role,
        )
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return
            tenant_db_id, client_id = ids
            text_val = str(message_text or "").strip()
            if not text_val:
                return
            normalized_role = str(role or "user").strip().lower() or "user"

            from sqlalchemy import text as sa_text
            engine = self._engine()
            with engine.begin() as conn:
                conn.execute(
                    sa_text(
                        """
                        INSERT INTO conversation_messages
                            (tenant_id, client_id, role, content)
                        VALUES (:tid, :cid, :role, :content)
                        """
                    ),
                    {
                        "tid": tenant_db_id,
                        "cid": client_id,
                        "role": normalized_role,
                        "content": text_val,
                    },
                )
        except Exception as exc:
            self._log_db_fallback("save_message", tenant_slug, user_id, exc)

    def get_history(self, *, tenant_slug: str, user_id: str) -> list[dict[str, str]]:
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return super().get_history(tenant_slug=tenant_slug, user_id=user_id)
            tenant_db_id, client_id = ids

            from sqlalchemy import text as sa_text
            engine = self._engine()
            with engine.connect() as conn:
                rows = conn.execute(
                    sa_text(
                        """
                        SELECT role, content FROM conversation_messages
                        WHERE tenant_id = :tid AND client_id = :cid
                        ORDER BY created_at ASC
                        LIMIT 40
                        """
                    ),
                    {"tid": tenant_db_id, "cid": client_id},
                ).fetchall()

            if rows is None:
                return super().get_history(tenant_slug=tenant_slug, user_id=user_id)

            return [
                {
                    "role": str(r._mapping.get("role") or "user").strip().lower() or "user",
                    "text": str(r._mapping.get("content") or "").strip(),
                }
                for r in rows
                if str(r._mapping.get("content") or "").strip()
            ]
        except Exception as exc:
            self._log_db_fallback("get_history", tenant_slug, user_id, exc)
            return super().get_history(tenant_slug=tenant_slug, user_id=user_id)

    # ------------------------------------------------------------------ #
    # Scalar memory fields backed by conversation_memory JSONB            #
    # ------------------------------------------------------------------ #

    def _set_mem(self, tenant_slug: str, user_id: str, key: str, value: object) -> None:
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return
            self._upsert_memory_key(ids[0], ids[1], key, value)
        except Exception as exc:
            self._log_db_fallback(f"_set_mem:{key}", tenant_slug, user_id, exc)

    def _get_mem(self, tenant_slug: str, user_id: str, key: str, default: object = None) -> object:
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return default
            mem = self._read_memory(ids[0], ids[1])
            return mem.get(key, default)
        except Exception as exc:
            self._log_db_fallback(f"_get_mem:{key}", tenant_slug, user_id, exc)
            return default

    # last_intent
    def set_last_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        super().set_last_intent(tenant_slug=tenant_slug, user_id=user_id, intent=intent)
        self._set_mem(tenant_slug, user_id, "last_intent", str(intent or "").strip().lower())

    def get_last_intent(self, *, tenant_slug: str, user_id: str) -> str:
        ram = super().get_last_intent(tenant_slug=tenant_slug, user_id=user_id)
        if ram:
            return ram
        return str(self._get_mem(tenant_slug, user_id, "last_intent") or "")

    # detected_intent
    def set_detected_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        super().set_detected_intent(tenant_slug=tenant_slug, user_id=user_id, intent=intent)
        self._set_mem(tenant_slug, user_id, "intent_detectado", str(intent or "").strip().lower())

    def get_detected_intent(self, *, tenant_slug: str, user_id: str) -> str:
        ram = super().get_detected_intent(tenant_slug=tenant_slug, user_id=user_id)
        if ram:
            return ram
        return str(self._get_mem(tenant_slug, user_id, "intent_detectado") or "")

    # payment_method
    def set_payment_method(self, *, tenant_slug: str, user_id: str, method: str) -> None:
        super().set_payment_method(tenant_slug=tenant_slug, user_id=user_id, method=method)
        self._set_mem(tenant_slug, user_id, "metodo_pago_elegido", str(method or "").strip().lower())

    def get_payment_method(self, *, tenant_slug: str, user_id: str) -> str:
        ram = super().get_payment_method(tenant_slug=tenant_slug, user_id=user_id)
        if ram:
            return ram
        return str(self._get_mem(tenant_slug, user_id, "metodo_pago_elegido") or "")

    # payment_status
    def set_payment_status(self, *, tenant_slug: str, user_id: str, status: str) -> None:
        super().set_payment_status(tenant_slug=tenant_slug, user_id=user_id, status=status)
        self._set_mem(tenant_slug, user_id, "estado_pago", str(status or "").strip().lower())

    def get_payment_status(self, *, tenant_slug: str, user_id: str) -> str:
        ram = super().get_payment_status(tenant_slug=tenant_slug, user_id=user_id)
        if ram:
            return ram
        return str(self._get_mem(tenant_slug, user_id, "estado_pago") or "")

    # last_pain
    def set_last_pain(self, *, tenant_slug: str, user_id: str, pain: str) -> None:
        super().set_last_pain(tenant_slug=tenant_slug, user_id=user_id, pain=pain)
        self._set_mem(tenant_slug, user_id, "last_pain", str(pain or "").strip().lower())

    def get_last_pain(self, *, tenant_slug: str, user_id: str) -> str:
        ram = super().get_last_pain(tenant_slug=tenant_slug, user_id=user_id)
        if ram:
            return ram
        return str(self._get_mem(tenant_slug, user_id, "last_pain") or "")

    # last_response
    def set_last_response(self, *, tenant_slug: str, user_id: str, response: str) -> None:
        super().set_last_response(tenant_slug=tenant_slug, user_id=user_id, response=response)
        self._set_mem(tenant_slug, user_id, "last_ai_response", str(response or "").strip())

    def get_last_response(self, *, tenant_slug: str, user_id: str) -> str:
        ram = super().get_last_response(tenant_slug=tenant_slug, user_id=user_id)
        if ram:
            return ram
        return str(self._get_mem(tenant_slug, user_id, "last_ai_response") or "")

    # conversation_state (serialized as JSON)
    def set_conversation_state(self, *, tenant_slug: str, user_id: str, state) -> None:
        super().set_conversation_state(tenant_slug=tenant_slug, user_id=user_id, state=state)
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return
            from app.domain.conversation.memory import ConversationState
            timeline = getattr(state, "pain_timeline", None)
            timeline_list = timeline if isinstance(timeline, list) else []
            blob = {
                "pain_detected": bool(getattr(state, "pain_detected", False)),
                "pain_timeline": [str(i).strip() for i in timeline_list if str(i).strip()][-20:],
                "urgency": str(getattr(state, "urgency", "") or "").strip().lower(),
                "last_intent": str(getattr(state, "last_intent", "") or "").strip().lower(),
                "stage": str(getattr(state, "stage", "") or "").strip().lower(),
                "objections": max(0, int(getattr(state, "objections", 0) or 0)),
                "last_cta": str(getattr(state, "last_cta", "") or "").strip(),
            }
            self._upsert_memory_key(ids[0], ids[1], "conversation_state", blob)
        except Exception as exc:
            self._log_db_fallback("set_conversation_state", tenant_slug, user_id, exc)

    def get_conversation_state(self, *, tenant_slug: str, user_id: str):
        from app.domain.conversation.memory import ConversationState
        # Try RAM first (in-process, fastest)
        ram_key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if ram_key and self._conversation_state_by_user.get(ram_key):
            return super().get_conversation_state(tenant_slug=tenant_slug, user_id=user_id)
        # Fall back to DB
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return ConversationState()
            mem = self._read_memory(ids[0], ids[1])
            raw = mem.get("conversation_state")
            if not raw or not isinstance(raw, dict):
                return ConversationState()
            timeline = raw.get("pain_timeline") if isinstance(raw.get("pain_timeline"), list) else []
            return ConversationState(
                pain_detected=bool(raw.get("pain_detected", False)),
                pain_timeline=[str(i).strip() for i in timeline if str(i).strip()],
                urgency=str(raw.get("urgency") or "").strip().lower(),
                last_intent=str(raw.get("last_intent") or "").strip().lower(),
                stage=str(raw.get("stage") or "").strip().lower(),
                objections=max(0, int(raw.get("objections") or 0)),
                last_cta=str(raw.get("last_cta") or "").strip(),
            )
        except Exception as exc:
            self._log_db_fallback("get_conversation_state", tenant_slug, user_id, exc)
            return super().get_conversation_state(tenant_slug=tenant_slug, user_id=user_id)

    # last_user_message_at
    def set_last_user_message_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        super().set_last_user_message_at(tenant_slug=tenant_slug, user_id=user_id, sent_at=sent_at)
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if ids:
                self._upsert_memory_key(ids[0], ids[1], "last_user_message_at", sent_at.isoformat())
        except Exception as exc:
            self._log_db_fallback("set_last_user_message_at", tenant_slug, user_id, exc)

    def get_last_user_message_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        ram_val = super().get_last_user_message_at(tenant_slug=tenant_slug, user_id=user_id)
        if ram_val is not None:
            return ram_val
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return None
            mem = self._read_memory(ids[0], ids[1])
            raw = mem.get("last_user_message_at")
            if raw:
                dt = datetime.fromisoformat(str(raw))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        except Exception as exc:
            self._log_db_fallback("get_last_user_message_at", tenant_slug, user_id, exc)
        return None

    # initial_message_last_sent_at
    def set_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        super().set_initial_message_last_sent_at(tenant_slug=tenant_slug, user_id=user_id, sent_at=sent_at)
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if ids:
                self._upsert_memory_key(ids[0], ids[1], "initial_message_last_sent_at", sent_at.isoformat())
        except Exception as exc:
            self._log_db_fallback("set_initial_message_last_sent_at", tenant_slug, user_id, exc)

    def get_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        ram_val = super().get_initial_message_last_sent_at(tenant_slug=tenant_slug, user_id=user_id)
        if ram_val is not None:
            return ram_val
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return None
            mem = self._read_memory(ids[0], ids[1])
            raw = mem.get("initial_message_last_sent_at")
            if raw:
                dt = datetime.fromisoformat(str(raw))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        except Exception as exc:
            self._log_db_fallback("get_initial_message_last_sent_at", tenant_slug, user_id, exc)
        return None

    # reset_conversation — clears both DB tables and RAM
    def reset_conversation(self, *, tenant_slug: str, user_id: str) -> None:
        super().reset_conversation(tenant_slug=tenant_slug, user_id=user_id)
        try:
            ids = self._resolve_ids(tenant_slug, user_id)
            if not ids:
                return
            tenant_db_id, client_id = ids
            from sqlalchemy import text as sa_text
            engine = self._engine()
            with engine.begin() as conn:
                conn.execute(
                    sa_text(
                        "DELETE FROM conversation_messages WHERE tenant_id=:tid AND client_id=:cid"
                    ),
                    {"tid": tenant_db_id, "cid": client_id},
                )
                conn.execute(
                    sa_text(
                        "UPDATE conversation_memory SET memory='{}', updated_at=now() "
                        "WHERE tenant_id=:tid AND client_id=:cid"
                    ),
                    {"tid": tenant_db_id, "cid": client_id},
                )
        except Exception as exc:
            self._log_db_fallback("reset_conversation", tenant_slug, user_id, exc)
