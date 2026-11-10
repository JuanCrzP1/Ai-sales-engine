"""Inteligencia artificial y área de pruebas de cada negocio.

- La clave de OpenRouter de cada negocio se guarda cifrada y nunca vuelve completa al panel.
- El área de pruebas conversa con el asistente usando la versión que se está editando (para probar antes de publicar) o la
  publicada, con la clave de ese negocio y en una conversación aislada de los clientes reales. El motor la ejecuta detrás del
  puerto `AssistantRunner`: esta capa no lo conoce.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Literal

from app.business_config_application.ports import AIKeyVerifier, AISettingsStorage, AssistantRunner
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.ai_settings import AICredentials, AISettings, AssistantTurn, KeyCheck, clean_api_key, clean_model
from app.domain.business_config.errors import (
    AIKeyMissingError,
    AssistantUnavailableError,
    FieldIssue,
    InvalidFieldsError,
    PaymentDataUnavailableError,
    PublicationError,
    SecretResolutionError,
)

ConfigSource = Literal["draft", "published"]
MAX_MESSAGE_CHARS = 1000
_SESSION_ID = re.compile(r"[0-9a-f]{32}")


@dataclass(frozen=True)
class PlaygroundReply:
    """Una respuesta del área de pruebas, con la conversación y la versión con la que se respondió."""

    session_id: str
    source: ConfigSource
    version: int
    turn: AssistantTurn


class AssistantLabService:
    def __init__(
        self,
        configs: BusinessConfigService,
        storage: AISettingsStorage,
        *,
        verifier: AIKeyVerifier | None = None,
        runner: AssistantRunner | None = None,
    ) -> None:
        self._configs = configs
        self._storage = storage
        self._verifier = verifier
        self._runner = runner

    # ------------------------------------------------------------------ inteligencia artificial

    def ai_settings(self, tenant_slug: str) -> AISettings:
        self._configs.get_business(tenant_slug)
        return self._storage.ai_settings(tenant_slug)

    def save_ai_settings(self, tenant_slug: str, *, model: str | None, api_key: str | None = None, clear_key: bool = False) -> AISettings:
        """Sin `api_key` se conserva la clave guardada; `clear_key` la quita. El modelo vacío vuelve al del motor."""
        self._configs.get_business(tenant_slug)
        key = clean_api_key(api_key) if api_key else None
        if key and clear_key:
            raise InvalidFieldsError("Elige entre cambiar la clave o quitarla.", [FieldIssue("api_key", "Elige entre cambiar la clave o quitarla.")])
        return self._storage.save_ai_settings(tenant_slug, model=clean_model(model), api_key=key, clear_key=clear_key)

    def verify_ai_key(self, tenant_slug: str) -> KeyCheck:
        credentials = self._credentials(tenant_slug)
        if self._verifier is None:
            raise AssistantUnavailableError("la comprobación de la clave no está disponible en este servidor")
        return self._verifier.verify(credentials)

    # ------------------------------------------------------------------ área de pruebas

    def talk(self, tenant_slug: str, *, message: str, source: ConfigSource = "draft", session_id: str | None = None) -> PlaygroundReply:
        text = str(message or "").strip()
        if not text or len(text) > MAX_MESSAGE_CHARS:
            raise InvalidFieldsError("Revisa el mensaje.", [FieldIssue("message", f"Escribe un mensaje de hasta {MAX_MESSAGE_CHARS} caracteres.")])
        session = self._session(session_id) if session_id else uuid.uuid4().hex
        runner = self._require_runner()
        credentials = self._credentials(tenant_slug)
        version = self._version(tenant_slug, source)
        try:
            sections = self._configs.compile_sections(tenant_slug, version)
        except SecretResolutionError as exc:
            raise PaymentDataUnavailableError("faltan datos de pago de esta versión: complétalos para probarla") from exc
        turn = runner.reply(tenant_slug=tenant_slug, sections=sections, credentials=credentials, session_id=session, message=text)
        return PlaygroundReply(session, source, version, turn)

    def reset(self, tenant_slug: str, session_id: str) -> None:
        self._configs.get_business(tenant_slug)
        self._require_runner().reset(tenant_slug=tenant_slug, session_id=self._session(session_id))

    # ------------------------------------------------------------------ apoyo

    def _credentials(self, tenant_slug: str) -> AICredentials:
        self._configs.get_business(tenant_slug)
        credentials = self._storage.ai_credentials(tenant_slug)
        if credentials is None:
            raise AIKeyMissingError(f"{tenant_slug}: este negocio no tiene clave de IA; agrégala en Inteligencia artificial")
        return credentials

    def _require_runner(self) -> AssistantRunner:
        if self._runner is None:
            raise AssistantUnavailableError("el área de pruebas no está disponible en este servidor")
        return self._runner

    def _version(self, tenant_slug: str, source: ConfigSource) -> int:
        summary = self._configs.get_business(tenant_slug)
        if source == "published":
            if summary.published_version is None:
                raise PublicationError(f"{tenant_slug}: todavía no hay una versión publicada")
            return summary.published_version
        version = summary.draft_version or summary.published_version or summary.latest_version
        if version is None:
            raise PublicationError(f"{tenant_slug}: todavía no hay ninguna versión guardada")
        return version

    @staticmethod
    def _session(session_id: str) -> str:
        if not _SESSION_ID.fullmatch(str(session_id or "")):
            raise InvalidFieldsError("La conversación no es válida.", [FieldIssue("session_id", "Empieza una conversación nueva.")])
        return session_id
