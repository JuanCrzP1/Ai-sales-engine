from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.domain.conversation.memory import ConversationState
from app.infrastructure.config.config_service import ConfigService
from app.utils.logger import logger


# ================================
# INITIAL MESSAGE HANDLING
# -------------------------------
# Este mensaje NO pertenece a la IA.
# Es configuracion del tenant (YAML).
# Se detecta solo para saludos puros.
# Se controla por actividad real del chat.
# ================================


def is_chat_active(last_user_message_at: datetime | None, now: datetime, window_minutes: int) -> bool:
    if not isinstance(last_user_message_at, datetime):
        return False

    if last_user_message_at.tzinfo is None:
        last_at = last_user_message_at.replace(tzinfo=timezone.utc)
    else:
        last_at = last_user_message_at.astimezone(timezone.utc)

    delta = now - last_at
    return delta.total_seconds() < max(0, window_minutes) * 60


def should_send_initial_message(*, message: str, last_user_message_at: datetime | None, config: dict) -> bool:
    payload = config if isinstance(config, dict) else {}
    initial_cfg = payload.get("initial_message") if isinstance(payload.get("initial_message"), dict) else {}

    if not bool(initial_cfg.get("enabled", False)):
        return False

    mode = str(initial_cfg.get("mode") or "smart").strip().lower() or "smart"

    if mode == "off":
        return False

    if not is_greeting_only(message):
        return False

    conversation_cfg = payload.get("conversation") if isinstance(payload.get("conversation"), dict) else {}
    try:
        active_window_minutes = int(conversation_cfg.get("active_window_minutes", 15) or 15)
    except (TypeError, ValueError):
        active_window_minutes = 15

    now = datetime.now(timezone.utc)
    if is_chat_active(last_user_message_at, now, active_window_minutes):
        return False

    return True


def normalize_text(text: str) -> str:
    value = str(text or "").strip().lower()

    value = unicodedata.normalize("NFD", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")

    translator = str.maketrans("", "", "¡!¿?.,;:")
    value = value.translate(translator)

    return " ".join(value.split())


def is_greeting_only(message: str) -> bool:
    normalized = normalize_text(message)

    if not normalized:
        return False

    greetings = {
        "hola",
        "holaa",
        "buenas",
        "hey",
        "holi",
        "que mas",
        "q mas",
        "qlq",
        "parce",
        "parce que mas",
        "amigo",
        "bro",
        "buen dia",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
    }

    greeting_starters = {
        "hola",
        "holaa",
        "buenas",
        "hey",
        "holi",
        "que mas",
        "q mas",
        "qlq",
        "parce",
        "amigo",
        "bro",
        "buen dia",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
    }

    intent_tokens = {
        "precio",
        "vale",
        "cuanto",
        "cuesta",
        "info",
        "informacion",
        "informaciono",
        "necesito",
        "quiero",
        "venden",
        "vendes",
        "pedido",
        "comprar",
        "comprarlo",
        "ayuda",
    }

    soft_tokens = {
        "hola",
        "holaa",
        "buenas",
        "hey",
        "holi",
        "que",
        "q",
        "mas",
        "parce",
        "parcero",
        "amigo",
        "bro",
        "buen",
        "dia",
        "dias",
        "tardes",
        "noches",
    }

    if normalized in greetings:
        return True

    words = normalized.split()

    if len(words) > 3:
        return False

    if any(word in intent_tokens for word in words):
        return False

    if any(normalized.startswith(greeting) for greeting in greeting_starters):
        return all(word in soft_tokens for word in words)

    return False


def get_conversation_state(last_message_at, config) -> str:
    if not isinstance(last_message_at, datetime):
        return "new"

    payload = config if isinstance(config, dict) else {}
    conversation_cfg = payload.get("conversation") if isinstance(payload.get("conversation"), dict) else {}

    try:
        active_window = int(conversation_cfg.get("active_window_minutes", 15) or 15)
    except (TypeError, ValueError):
        active_window = 15

    try:
        reset_hours = int(conversation_cfg.get("reset_hours", 4) or 4)
    except (TypeError, ValueError):
        reset_hours = 4

    now = datetime.now(timezone.utc)
    if last_message_at.tzinfo is None:
        last_at = last_message_at.replace(tzinfo=timezone.utc)
    else:
        last_at = last_message_at.astimezone(timezone.utc)

    delta = now - last_at

    if delta < timedelta(minutes=max(0, active_window)):
        return "active"

    if delta < timedelta(hours=max(0, reset_hours)):
        return "warm"

    return "cold"


@dataclass
class ConversationResult:
    runtime_yaml: dict
    user_id: str
    intent: str
    early_response: str | None
    early_source: str | None = None


class ConversationFlow:
    def __init__(self, *, memory_service, demo_service, config_service: ConfigService | None = None) -> None:
        self.memory = memory_service
        self.demo = demo_service
        self.config = config_service or ConfigService()

    @staticmethod
    def _normalize_user_id(user_id: str | None) -> str:
        normalized = str(user_id or "").strip().lower()
        return normalized or "anonymous"

    @staticmethod
    def is_greeting_only(message: str) -> bool:
        return is_greeting_only(message)

    def _load_initial_config(self, tenant_slug: str, runtime_yaml: dict) -> dict:
        runtime_config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
        initial_cfg = runtime_config.get("initial_message") if isinstance(runtime_config.get("initial_message"), dict) else {}
        if initial_cfg:
            return initial_cfg

        initial_payload = self.config.load_initial_message(client_id=tenant_slug)
        loaded_cfg = initial_payload.get("initial_message") if isinstance(initial_payload.get("initial_message"), dict) else {}
        return loaded_cfg if isinstance(loaded_cfg, dict) else {}

    @staticmethod
    def _set_stage(runtime_yaml: dict, stage: str) -> None:
        runtime_yaml["conversation_stage"] = stage
        runtime_yaml["lead_stage"] = stage

    def _inject_conversation_history(self, *, tenant_slug: str, user_id: str, conversation_history: list, runtime_yaml: dict) -> str:
        history = self.memory.get_history(tenant_slug=tenant_slug, user_id=user_id)
        base_history = conversation_history if isinstance(conversation_history, list) else []
        runtime_yaml["conversation_history"] = [*history, *base_history]
        runtime_yaml["user_id"] = user_id

        previous_user_message = ""
        for item in reversed(history):
            if isinstance(item, dict):
                if item.get("role", "user") == "user":
                    previous_user_message = str(item.get("text") or "").strip()
                    break
            else:
                previous_user_message = str(item or "").strip()
                break
        if previous_user_message:
            runtime_yaml["previous_user_message"] = previous_user_message
        return previous_user_message

    def _apply_persisted_memory_state(self, *, tenant_slug: str, user_id: str, runtime_yaml: dict) -> tuple[str, str, str]:
        persisted_mode = str(self.memory.get_mode(tenant_slug=tenant_slug, user_id=user_id) or "").strip().lower()
        persisted_intent = str(self.memory.get_last_intent(tenant_slug=tenant_slug, user_id=user_id) or "").strip().lower()
        persisted_pain = str(self.memory.get_last_pain(tenant_slug=tenant_slug, user_id=user_id) or "").strip().lower()

        if persisted_mode:
            runtime_yaml["mode"] = persisted_mode
        if persisted_intent:
            runtime_yaml["last_intent"] = persisted_intent
        if persisted_pain:
            runtime_yaml["active_pain"] = persisted_pain
            runtime_yaml["pain_text"] = persisted_pain

        return persisted_mode, persisted_intent, persisted_pain

    def _save_runtime_memory(
        self,
        *,
        tenant_slug: str,
        user_id: str,
        user_message: str,
        intent: str,
        stage: str,
        persist_signals: bool = False,
    ) -> None:
        saved_at = datetime.now(timezone.utc)
        logger.info(
            {
                "event": "saving_last_user_message_at",
                "user_id": str(user_id or "").strip().lower(),
                "tenant": str(tenant_slug or "").strip().lower(),
                "timestamp": saved_at,
            }
        )
        self.memory.save_message(tenant_slug=tenant_slug, user_id=user_id, message_text=user_message)
        self.memory.set_last_user_message_at(
            tenant_slug=tenant_slug,
            user_id=user_id,
            sent_at=saved_at,
        )
        if persist_signals:
            self.memory.set_last_intent(tenant_slug=tenant_slug, user_id=user_id, intent=intent)
            self.memory.set_stage(tenant_slug=tenant_slug, user_id=user_id, stage=stage)

    def handle_initial_message(
        self,
        user_id: str,
        tenant_slug: str,
        user_message: str,
        runtime_yaml: dict,
        *,
        force_send: bool = False,
    ) -> tuple[str, str] | None:
        initial_cfg = self._load_initial_config(tenant_slug, runtime_yaml)
        initial_text = str(initial_cfg.get("text") or "").strip()
        if not initial_text:
            return None

        if force_send:
            if not bool(initial_cfg.get("enabled", False)):
                return None

            initial_sent_at = self.memory.get_initial_message_last_sent_at(tenant_slug=tenant_slug, user_id=user_id)
            if isinstance(initial_sent_at, datetime):
                return None

            now = datetime.now(timezone.utc)
            self.memory.set_initial_message_last_sent_at(
                tenant_slug=tenant_slug,
                user_id=user_id,
                sent_at=now,
            )
            self._set_stage(runtime_yaml, "connection")
            self._save_runtime_memory(
                tenant_slug=tenant_slug,
                user_id=user_id,
                user_message=user_message,
                intent="",
                stage="",
            )
            return initial_text, "initial_message"

        last_user_message_at = self.memory.get_last_user_message_at(tenant_slug=tenant_slug, user_id=user_id)
        runtime_config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
        conversation_cfg = runtime_config.get("conversation") if isinstance(runtime_config.get("conversation"), dict) else {}
        if not should_send_initial_message(
            message=user_message,
            last_user_message_at=last_user_message_at,
            config={"initial_message": initial_cfg, "conversation": conversation_cfg},
        ):
            return None

        now = datetime.now(timezone.utc)

        self.memory.set_initial_message_last_sent_at(
            tenant_slug=tenant_slug,
            user_id=user_id,
            sent_at=now,
        )
        self._set_stage(runtime_yaml, "connection")

        self._save_runtime_memory(
            tenant_slug=tenant_slug,
            user_id=user_id,
            user_message=user_message,
            intent="",
            stage="",
        )

        return initial_text, "initial_message"

    def _build_demo_result(self, *, tenant_slug: str, user_id: str, user_message: str, runtime_yaml: dict) -> ConversationResult:
        self.demo.activate(tenant_slug, user_id)
        runtime_yaml["demo_input"] = True
        runtime_yaml["mode"] = "demo"
        self._set_stage(runtime_yaml, "connection")

        self._save_runtime_memory(
            tenant_slug=tenant_slug,
            user_id=user_id,
            user_message=user_message,
            intent="",
            stage="",
        )
        self.memory.set_mode(tenant_slug=tenant_slug, user_id=user_id, mode="demo")
        return ConversationResult(runtime_yaml=runtime_yaml, user_id=user_id, intent="", early_response=self.demo.handle(), early_source="demo")

    def _build_persisted_demo_result(self, *, tenant_slug: str, user_id: str, user_message: str, runtime_yaml: dict) -> ConversationResult:
        runtime_yaml["mode"] = "demo"
        runtime_yaml["demo_input"] = True
        current_stage = str(self.memory.get_stage(tenant_slug=tenant_slug, user_id=user_id) or "").strip().lower() or "connection"
        self._set_stage(runtime_yaml, current_stage)

        self._save_runtime_memory(
            tenant_slug=tenant_slug,
            user_id=user_id,
            user_message=user_message,
            intent="",
            stage="",
        )
        return ConversationResult(runtime_yaml=runtime_yaml, user_id=user_id, intent="", early_response=None)

    def process(
        self,
        *,
        tenant,
        tenant_slug: str,
        user_id: str | None,
        user_message: str,
        conversation_history: list,
        runtime_yaml: dict,
    ) -> ConversationResult:
        normalized_user_id = self._normalize_user_id(user_id)
        runtime_config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
        last_message_at = self.memory.get_last_user_message_at(tenant_slug=tenant_slug, user_id=normalized_user_id)
        logger.info(
            {
                "event": "debug_conversation_state",
                "user_id": normalized_user_id,
                "tenant": str(tenant_slug or "").strip().lower(),
                "last_message_at": last_message_at,
            }
        )
        temporal_state = get_conversation_state(last_message_at, runtime_config)
        logger.info(
            {
                "event": "debug_temporal_state",
                "user_id": normalized_user_id,
                "tenant": str(tenant_slug or "").strip().lower(),
                "state": temporal_state,
            }
        )
        if temporal_state == "cold":
            # 5B: preservar memoria comercial durable antes del reset total
            _cold_pain = str(
                self.memory.get_last_pain(tenant_slug=tenant_slug, user_id=normalized_user_id) or ""
            ).strip()
            _cold_state = self.memory.get_conversation_state(
                tenant_slug=tenant_slug, user_id=normalized_user_id
            )
            _cold_timeline = list(getattr(_cold_state, "pain_timeline", None) or [])

            self.memory.reset_conversation(tenant_slug=tenant_slug, user_id=normalized_user_id)

            # Restaurar únicamente last_pain y pain_timeline para sales_memory_hint
            if _cold_pain:
                self.memory.set_last_pain(
                    tenant_slug=tenant_slug, user_id=normalized_user_id, pain=_cold_pain
                )
            if _cold_timeline:
                self.memory.set_conversation_state(
                    tenant_slug=tenant_slug,
                    user_id=normalized_user_id,
                    state=ConversationState(pain_timeline=_cold_timeline),
                )
            runtime_yaml["conversation_state"] = "new"
        else:
            runtime_yaml["conversation_state"] = temporal_state

        self._inject_conversation_history(
            tenant_slug=tenant_slug,
            user_id=normalized_user_id,
            conversation_history=conversation_history,
            runtime_yaml=runtime_yaml,
        )
        persisted_mode, _persisted_intent, _persisted_pain = self._apply_persisted_memory_state(
            tenant_slug=tenant_slug,
            user_id=normalized_user_id,
            runtime_yaml=runtime_yaml,
        )

        initial_message = None
        if str(runtime_yaml.get("conversation_state") or "").strip().lower() == "new" and is_greeting_only(user_message):
            initial_message = self.handle_initial_message(
                user_id=normalized_user_id,
                tenant_slug=tenant_slug,
                user_message=user_message,
                runtime_yaml=runtime_yaml,
            )
        if initial_message:
            initial_text, initial_source = initial_message
            logger.info(
                {
                    "event": "backend_initial_message",
                    "tenant": str(tenant_slug or "").strip().lower(),
                    "user_id": normalized_user_id,
                    "conversation_state": str(runtime_yaml.get("conversation_state") or "").strip().lower(),
                }
            )
            return ConversationResult(
                runtime_yaml=runtime_yaml,
                user_id=normalized_user_id,
                intent="greeting",
                early_response=initial_text,
                early_source=initial_source,
            )

        demo_activation = self.demo.should_activate(tenant, user_message)
        if demo_activation:
            return self._build_demo_result(
                tenant_slug=tenant_slug,
                user_id=normalized_user_id,
                user_message=user_message,
                runtime_yaml=runtime_yaml,
            )

        if persisted_mode == "demo":
            return self._build_persisted_demo_result(
                tenant_slug=tenant_slug,
                user_id=normalized_user_id,
                user_message=user_message,
                runtime_yaml=runtime_yaml,
            )

        runtime_yaml["demo_input"] = False
        persisted_stage = str(self.memory.get_stage(tenant_slug=tenant_slug, user_id=normalized_user_id) or "").strip().lower()
        if persisted_stage:
            self._set_stage(runtime_yaml, persisted_stage)
        self._save_runtime_memory(
            tenant_slug=tenant_slug,
            user_id=normalized_user_id,
            user_message=user_message,
            intent="",
            stage="",
        )

        return ConversationResult(
            runtime_yaml=runtime_yaml,
            user_id=normalized_user_id,
            intent="",
            early_response=None,
        )
