"""El motor real respondiendo en el área de pruebas del panel (implementa `AssistantRunner`).

- Usa la configuración que se le entrega (la versión que se está probando) y la clave de IA de ese negocio, por el mismo camino
  que un mensaje real.
- Cada conversación tiene su propia memoria en RAM: no toca la base de los clientes reales ni sus conversaciones.
- Las conversaciones se identifican por negocio y sesión: una sesión de un negocio no sirve en otro.
- Se olvidan tras un tiempo sin uso y hay un máximo; en ese caso, se descarta la usada hace más tiempo.
"""
from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from types import SimpleNamespace

from app.application.ai_pipeline import AIPipeline
from app.application.runtime import runtime_from_sections
from app.domain.business_config.ai_settings import AICredentials, AssistantTurn
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository

MAX_SESSIONS = 200
IDLE_SECONDS = 60 * 60


@dataclass
class _Session:
    memory: MemoryDomainService
    last_used: float


class EngineAssistantRunner:
    def __init__(
        self,
        *,
        max_sessions: int = MAX_SESSIONS,
        idle_seconds: float = IDLE_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        pipeline_factory: Callable[..., AIPipeline] = AIPipeline,
    ) -> None:
        self._max_sessions = max_sessions
        self._idle_seconds = idle_seconds
        self._clock = clock
        self._pipeline_factory = pipeline_factory
        self._sessions: OrderedDict[tuple[str, str], _Session] = OrderedDict()
        self._lock = threading.Lock()

    def reply(self, *, tenant_slug: str, sections: dict[str, dict], credentials: AICredentials, session_id: str, message: str) -> AssistantTurn:
        runtime = runtime_from_sections(tenant_slug, sections)
        pipeline = self._pipeline_factory(
            memory_service=self._memory(tenant_slug, session_id),
            runtime_loader=lambda _slug, **_options: copy.deepcopy(runtime),
            ai_loader=lambda _slug: credentials,
        )
        answer, ai_used, metadata = pipeline.run(
            tenant=SimpleNamespace(slug=tenant_slug, name=tenant_slug, id=tenant_slug),
            user_message=message,
            user_id=f"prueba-{session_id}",
            bot_config=None,
            conversation_history=[],
            faq_results=[],
            yaml_config=None,
            include_metadata=True,
        )
        intent = str((metadata or {}).get("intent") or "").strip() or None
        return AssistantTurn(reply=str(answer or ""), intent=intent, ai_answered=bool(ai_used), handoff=bool((metadata or {}).get("handoff")))

    def reset(self, *, tenant_slug: str, session_id: str) -> None:
        with self._lock:
            self._sessions.pop((tenant_slug, session_id), None)

    def _memory(self, tenant_slug: str, session_id: str) -> MemoryDomainService:
        now = self._clock()
        key = (tenant_slug, session_id)
        with self._lock:
            for stale in [item for item, session in self._sessions.items() if now - session.last_used > self._idle_seconds]:
                del self._sessions[stale]
            session = self._sessions.get(key)
            if session is None:
                session = self._sessions[key] = _Session(MemoryDomainService(MemoryRepository()), now)
            session.last_used = now
            self._sessions.move_to_end(key)
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)
            return session.memory
