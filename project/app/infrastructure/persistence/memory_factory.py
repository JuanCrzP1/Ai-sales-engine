"""Qué memoria usa el motor: la de la base si es PostgreSQL (la nube y este equipo); en RAM si es otra (el SQLite de las pruebas).

Se decide una vez, al arrancar, por la base configurada (`DATABASE_URL`). Fuera de las pruebas, una memoria en RAM deja el aviso
`memoria_en_ram`: no se comparte entre servidores ni sobrevive a un reinicio.
"""
from __future__ import annotations

from app.domain.conversation.memory import MemoryRepositoryPort
from app.infrastructure.persistence.memory_repository import MemoryRepository
from app.infrastructure.persistence.sql_memory import SQLMemoryRepository
from app.utils.logger import logger


def build_memory_repository() -> MemoryRepositoryPort:
    from app.config import settings
    from app.infrastructure.db.connection import get_engine

    if get_engine().dialect.name == "postgresql":
        return SQLMemoryRepository()
    if str(getattr(settings, "mode", "") or "").strip().lower() != "test":
        logger.warning("memoria_en_ram", extra={"database": get_engine().dialect.name})
    return MemoryRepository()
