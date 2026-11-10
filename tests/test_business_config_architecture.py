"""Arquitectura de BusinessConfig: cada capa depende solo de lo que le corresponde y no hay ciclos.

Lee el código sin ejecutarlo. Cuenta también las importaciones dentro de funciones y las que solo sirven para anotar tipos: un
ciclo "solo de tipos" sigue siendo un acoplamiento. El panel tiene su propia comprobación en
`apps/admin-web/src/test/architecture.test.ts`.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
SCHEMA_PATH = PROJECT_DIR / "config" / "contracts" / "v1" / "business-config.schema.json"

DOMAIN = "app.domain.business_config"
APPLICATION = "app.business_config_application"
PERSISTENCE = "app.infrastructure.business_config"
API = "app.admin_api"
BRIDGE = (
    "app.application.runtime.tenant_runtime_loader",
    "app.infrastructure.config.business_config_store",
    "app.infrastructure.config.legacy_field_catalog",
    "app.infrastructure.config.legacy_store_migration",
    "app.infrastructure.config.legacy_yaml_importer",
    "app.infrastructure.config.payment_secrets",
)
# La única puerta del motor hacia el almacén: solo lee lo publicado y nunca crea ni escribe.
ENGINE_GATEWAY = f"{PERSISTENCE}.runtime_access"

# Qué puede importar cada capa, del proyecto y de fuera. Nadie puede importar el motor.
INTERNAL = {
    DOMAIN: (DOMAIN,),
    APPLICATION: (APPLICATION, DOMAIN),
    PERSISTENCE: (PERSISTENCE, APPLICATION, DOMAIN),
    API: (API, APPLICATION, DOMAIN),
}
THIRD_PARTY = {
    DOMAIN: {"pydantic"},
    APPLICATION: set(),
    PERSISTENCE: {"cryptography", "sqlalchemy"},
    API: {"fastapi", "pydantic"},
}
# Única excepción, temporal: la ruta de importación inicial lee los YAML y se retira con ellos en la Fase 4.
API_EXCEPTIONS = {"app.infrastructure.config.config_service", "app.infrastructure.config.legacy_store_migration"}

TECHNICAL_NAME = re.compile(r"api[_-]?key|token|passw|credential|secret(?!_ref)|openrouter|openai|model_name|database|dsn|webhook|jwt|ngrok|\bhost\b|\bport\b", re.I)


def _module_path(name: str) -> Path:
    base = PROJECT_DIR / name.replace(".", "/")
    return base / "__init__.py" if base.is_dir() else base.with_suffix(".py")


def _layer_modules(layer: str) -> dict[str, Path]:
    modules = {}
    for path in (PROJECT_DIR / layer.replace(".", "/")).rglob("*.py"):
        name = ".".join(path.relative_to(PROJECT_DIR).with_suffix("").parts).removesuffix(".__init__")
        modules[name] = path
    return modules


def _imports(name: str, path: Path) -> set[str]:
    """Lo que importa un módulo, cada `from x import y` como `x` y como `x.y`: `y` puede ser un submódulo."""
    package = name if path.name == "__init__.py" else name.rpartition(".")[0]
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".")
                base = ".".join(parts[: len(parts) - node.level + 1] + ([base] if base else []))
            found.add(base)
            found.update(f"{base}.{alias.name}" for alias in node.names)
    return found


def _violations(layer: str) -> Iterator[str]:
    allowed = INTERNAL[layer]
    for name, path in _layer_modules(layer).items():
        for target in _imports(name, path):
            top = target.partition(".")[0]
            if top == "app":
                inside = any(target == prefix or target.startswith(f"{prefix}.") for prefix in allowed)
                if not inside and not (layer == API and any(target.startswith(item) for item in API_EXCEPTIONS)):
                    yield f"{name} -> {target}"
            elif top not in sys.stdlib_module_names and top not in THIRD_PARTY[layer]:
                yield f"{name} -> {target}"


def _graph() -> dict[str, set[str]]:
    modules: dict[str, Path] = {name: _module_path(name) for name in BRIDGE}
    for layer in INTERNAL:
        modules.update(_layer_modules(layer))
    return {name: {target for target in _imports(name, path) if target in modules and target != name} for name, path in modules.items()}


def _cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    found: list[list[str]] = []
    finished: set[str] = set()

    def _visit(node: str, path: list[str]) -> None:
        for neighbour in sorted(graph.get(node, ())):
            if neighbour in path:
                found.append([*path[path.index(neighbour) :], neighbour])
            elif neighbour not in finished:
                _visit(neighbour, [*path, neighbour])
        finished.add(node)

    for node in sorted(graph):
        if node not in finished:
            _visit(node, [node])
    return found


@pytest.mark.parametrize("layer", list(INTERNAL))
def test_each_layer_only_depends_on_what_it_should(layer):
    assert _layer_modules(layer), "la comprobación debe ver los módulos de la capa"
    assert sorted(_violations(layer)) == []


def test_there_are_no_import_cycles():
    graph = _graph()
    assert f"{DOMAIN}.compiler" in graph[f"{APPLICATION}.service"], "la comprobación debe ver las dependencias reales"
    assert _cycles(graph) == []


def test_the_cycle_check_detects_cycles():
    assert _cycles({"a": {"b"}, "b": {"c"}, "c": {"a"}}) == [["a", "b", "c", "a"]]
    assert _cycles({"a": {"b"}, "b": set()}) == []


def test_the_layer_check_detects_a_forbidden_import(tmp_path, monkeypatch):
    package = tmp_path / "app" / "domain" / "business_config"
    package.mkdir(parents=True)
    (package / "malo.py").write_text("from sqlalchemy import select\nfrom app.infrastructure.business_config import tables\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "PROJECT_DIR", tmp_path)
    assert len(list(_violations(DOMAIN))) == 4


def _engine_modules() -> dict[str, Path]:
    """Todo `app` salvo las capas de BusinessConfig: el motor y sus adaptadores."""
    modules = _layer_modules("app")
    return {name: path for name, path in modules.items() if not any(name == layer or name.startswith(f"{layer}.") for layer in INTERNAL)}


def test_the_engine_reaches_the_store_only_through_its_gateway():
    engine = _engine_modules()
    assert "app.application.runtime.tenant_runtime_loader" in engine, "la comprobación debe ver el motor"
    reaching = {
        f"{name} -> {target}"
        for name, path in engine.items()
        for target in _imports(name, path)
        if target.startswith(f"{PERSISTENCE}.") and not (target == ENGINE_GATEWAY or target.startswith(f"{ENGINE_GATEWAY}."))
    }
    assert sorted(reaching) == []
    assert any(target.startswith(ENGINE_GATEWAY) for target in _imports("app.application.runtime.tenant_runtime_loader", engine["app.application.runtime.tenant_runtime_loader"]))


def test_the_routes_only_talk_to_the_service():
    imported = _imports(f"{API}.routes", _module_path(f"{API}.routes"))
    forbidden = ("sqlalchemy", PERSISTENCE, f"{DOMAIN}.compiler", f"{DOMAIN}.diagnostics", f"{DOMAIN}.contract", f"{DOMAIN}.records")
    assert [target for target in imported if target.startswith(forbidden)] == []
    assert f"{APPLICATION}.service.BusinessConfigService" in imported


def test_the_commercial_contract_has_no_technical_fields():
    names: set[str] = set()

    def _collect(node) -> None:
        if isinstance(node, dict):
            names.update(node.get("properties") or {})
            for value in node.values():
                _collect(value)
        elif isinstance(node, list):
            for value in node:
                _collect(value)

    _collect(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    assert "secret_ref" in names and "identity" in names, "la comprobación debe ver los campos del contrato"
    assert sorted(name for name in names if TECHNICAL_NAME.search(name)) == []
