## ========================================
## ARCHIVO: test_memory_repository_contract.py
##
## QUÉ VALIDA:
## Contrato mínimo activo de MemoryRepository.
##
## POR QUÉ ES CRÍTICO:
## Garantiza consistencia de la memoria conversacional usada por el runtime.
##
## QUÉ PROTEGE:
## Persistencia de contexto y aislamiento entre tenants/usuarios.
## ========================================

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.infrastructure.persistence.memory_repository import MemoryRepository


## ----------------------------------------
## QUÉ HACE ESTE TEST:
def test_update_and_get_last_user_message_at() -> None:
    repo = MemoryRepository()
    ts = datetime.now(timezone.utc) - timedelta(minutes=10)

    repo.update_last_user_message_at("tenant_a", "user_1", ts)

    mem = repo.get_memory("tenant_a", "user_1")
    assert mem.get("last_user_message_at") == ts


## ----------------------------------------
## QUÉ HACE ESTE TEST:
def test_update_and_get_initial_message_last_sent_at() -> None:
    repo = MemoryRepository()
    ts = datetime.now(timezone.utc) - timedelta(hours=1)

    repo.update_initial_message_last_sent_at("tenant_b", "user_2", ts)

    mem = repo.get_memory("tenant_b", "user_2")
    assert mem.get("initial_message_last_sent_at") == ts


## ----------------------------------------
## QUÉ HACE ESTE TEST:
def test_multiple_users_are_isolated() -> None:
    repo = MemoryRepository()
    ts_a = datetime.now(timezone.utc) - timedelta(minutes=5)
    ts_b = datetime.now(timezone.utc) - timedelta(hours=2)

    repo.update_last_user_message_at("tenant_x", "alice", ts_a)
    repo.update_last_user_message_at("tenant_x", "bob", ts_b)

    mem_a = repo.get_memory("tenant_x", "alice")
    mem_b = repo.get_memory("tenant_x", "bob")
    mem_unknown = repo.get_memory("tenant_x", "charlie")

    assert mem_a.get("last_user_message_at") == ts_a
    assert mem_b.get("last_user_message_at") == ts_b
    assert mem_unknown.get("last_user_message_at") is None


## ----------------------------------------
## QUÉ HACE ESTE TEST:
def test_memory_repository_updates_last_user_message_at() -> None:
    repo = MemoryRepository()

    ts = datetime.now(timezone.utc) - timedelta(minutes=3)
    repo.update_last_user_message_at("tenant_prod", "user_prod", ts)
    mem = repo.get_memory("tenant_prod", "user_prod")
    assert mem.get("last_user_message_at") == ts


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que MemoryRepository exponga contexto comercial reciente.
##
## POR QUÉ ES IMPORTANTE:
## El runtime necesita recordar último mensaje, última intención y última respuesta.
##
## QUÉ PROTEGE:
## Contrato mínimo de memoria comercial sin lógica adicional en backend.
## ----------------------------------------
def test_memory_repository_exposes_recent_commercial_context() -> None:
    repo = MemoryRepository()
    repo.save_message(tenant_slug="tenant_prod", user_id="user_ctx", message_text="tengo muchos mensajes")
    repo.set_last_intent(tenant_slug="tenant_prod", user_id="user_ctx", intent="pain")
    repo.set_last_response(tenant_slug="tenant_prod", user_id="user_ctx", response="te ayudo a ordenarlos")

    mem = repo.get_memory("tenant_prod", "user_ctx")

    assert mem.get("last_user_message") == "tengo muchos mensajes"
    assert mem.get("last_intent") == "pain"
    assert mem.get("last_ai_response") == "te ayudo a ordenarlos"
