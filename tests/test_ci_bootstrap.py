## ========================================
## ARCHIVO: test_ci_bootstrap.py
##
## QUÉ VALIDA:
##   Que la configuración sea "collection-safe": importar app.config NUNCA debe
##   abortar, y en contexto de test debe resolver una DATABASE_URL usable
##   (sqlite in-memory) sin depender de .env local, DATABASE_URL ni PostgreSQL.
##   Que la validación estricta de producción siga existiendo, pero en startup.
##
## POR QUÉ ES CRÍTICO:
##   Impide que se reintroduzca el fallo de CI "DATABASE_URL es obligatorio"
##   durante la fase de collection de pytest.
##
## NOTA: app.config es un MÓDULO (no paquete); el sub-paquete settings se carga
##   con nombre sintético. Por eso aquí se usa SOLO la API pública re-exportada.
## ========================================

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import app.config as config
from app.config import is_test_context, settings, validate_database_url


# ---------------------------------------------------------------------------
# 1. Import de app.config es seguro: no abortó y dejó una URL usable.
#    Si alguien reintroduce un raise en import, CI cae en collection y esta
#    garantía deja de cumplirse.
# ---------------------------------------------------------------------------

def test_app_config_import_is_collection_safe():
    assert str(settings.database_url or "").strip() != ""


def test_validate_database_url_is_public_api():
    assert hasattr(config, "validate_database_url")
    assert callable(config.validate_database_url)
    assert callable(is_test_context)


# ---------------------------------------------------------------------------
# 2. Detección de contexto de test sin depender de PYTEST_CURRENT_TEST
#    (presente vía "pytest" in sys.modules durante toda la sesión).
# ---------------------------------------------------------------------------

def test_is_test_context_true_under_pytest():
    assert is_test_context() is True


def test_default_detection_resolves_sqlite_in_test():
    # Sin forzar is_test: bajo pytest debe resolver sqlite cuando no hay URL.
    assert validate_database_url("", is_test=None) == "sqlite:///:memory:"


# ---------------------------------------------------------------------------
# 3. En contexto de test sin DATABASE_URL -> sqlite in-memory (no raise).
# ---------------------------------------------------------------------------

def test_validate_defaults_to_sqlite_in_test():
    assert validate_database_url("", is_test=True) == "sqlite:///:memory:"


# ---------------------------------------------------------------------------
# 4. En producción (no test) sin DATABASE_URL -> RuntimeError (fail-fast).
# ---------------------------------------------------------------------------

def test_validate_requires_url_in_production():
    with pytest.raises(RuntimeError, match="DATABASE_URL es obligatorio"):
        validate_database_url("", is_test=False)


# ---------------------------------------------------------------------------
# 5. sqlite prohibido fuera de test.
# ---------------------------------------------------------------------------

def test_validate_rejects_sqlite_in_production():
    with pytest.raises(RuntimeError, match="sqlite solo está permitido"):
        validate_database_url("sqlite:///file.db", is_test=False)


# ---------------------------------------------------------------------------
# 6. URL que no es PostgreSQL+psycopg ni sqlite -> rechazada.
# ---------------------------------------------------------------------------

def test_validate_rejects_non_postgres_url():
    with pytest.raises(RuntimeError, match="PostgreSQL con psycopg"):
        validate_database_url("mysql://user:pass@host/db", is_test=False)


# ---------------------------------------------------------------------------
# 7. URL PostgreSQL+psycopg válida en producción -> aceptada.
# ---------------------------------------------------------------------------

def test_validate_accepts_postgres_url_in_production():
    url = "postgresql+psycopg://user:pass@localhost:5432/app"
    assert validate_database_url(url, is_test=False) == url


# ---------------------------------------------------------------------------
# 8. La validación con argumentos explícitos NO muta settings.database_url.
# ---------------------------------------------------------------------------

def test_explicit_validation_does_not_mutate_settings():
    before = settings.database_url
    validate_database_url("postgresql+psycopg://x:y@h/d", is_test=False)
    assert settings.database_url == before
