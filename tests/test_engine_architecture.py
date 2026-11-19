"""Las capas del motor (`project/app`): cada pieza en la que le corresponde, y las dependencias en una sola dirección.

- `domain/`: las reglas, sin depender de nada del motor (ni aplicación, ni infraestructura, ni la API, ni los ajustes).
- `application/`: los casos de uso (el turno del asistente, los canales, la atención humana). La puerta de los canales es
  `application/assistant_service.py`.
- `infrastructure/`: lo que habla con el exterior (el modelo de IA, la base, los canales, el correo). No usa la capa de aplicación
  ni la API: la aplicación la usa a ella.
- `api/`: las rutas del motor.

`app/services/` mezclaba las tres (la puerta de los canales, el cliente de OpenRouter, el lector de la respuesta del modelo) y se
ordenó el 19 de noviembre de 2026. El almacén del panel (`infrastructure/business_config`, `infrastructure/notifications`) sigue
sus propias reglas de puertos con `business_config_application` (`test_business_config_architecture.py`).
"""
from __future__ import annotations

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "project" / "app"
# Pendiente conocido, anterior al orden de las capas: el constructor del prompt arma la configuración del mensaje con la capa de
# aplicación (importación dentro de la función, para evitar un ciclo). Se quita cuando quien lo llama le pase el runtime ya armado.
KNOWN_EXCEPTIONS = {("app.infrastructure.ai.prompting.builder.prompt_builder", "app.application.runtime.runtime_yaml_builder")}


def _modules() -> dict[str, Path]:
    modules = {}
    for path in APP_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        parts = list(path.relative_to(APP_DIR.parent).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules[".".join(parts)] = path
    return modules


def _imports(path: Path) -> set[str]:
    """Todo lo que importa el módulo, también dentro de funciones."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def _crossing(layer: str, forbidden: tuple[str, ...]) -> list[str]:
    return sorted(
        f"{name} -> {target}"
        for name, path in _modules().items()
        if name == layer or name.startswith(f"{layer}.")
        for target in _imports(path)
        if any(target == other or target.startswith(f"{other}.") for other in forbidden) and (name, target) not in KNOWN_EXCEPTIONS
    )


def test_the_old_services_package_is_gone():
    # Sin código: una carpeta vacía que deja la caché de Python no cuenta (git no la registra).
    assert not list((APP_DIR / "services").rglob("*.py"))
    assert not [name for name in _modules() if name.startswith("app.services")]


def test_the_domain_depends_on_nothing_of_the_engine():
    assert _crossing("app.domain", ("app.application", "app.infrastructure", "app.api", "app.admin_api", "app.config", "app.main")) == []


def test_the_infrastructure_never_uses_the_application_or_the_api():
    assert _crossing("app.infrastructure", ("app.application", "app.api", "app.main")) == []


def test_the_known_exception_still_exists_until_it_is_fixed():
    """Si se arregla, esta lista se vacía: la prueba avisa para no dejar una excepción que ya no hace falta."""
    modules = _modules()
    for name, target in KNOWN_EXCEPTIONS:
        assert target in _imports(modules[name]), f"{name} ya no importa {target}: quítalo de KNOWN_EXCEPTIONS"


def test_each_piece_lives_in_its_layer():
    modules = _modules()
    for name in (
        "app.application.assistant_service",
        "app.infrastructure.ai.llm_runtime",
        "app.infrastructure.ai.openrouter_client",
        "app.infrastructure.ai.ai_orchestrator",
        "app.infrastructure.ai.structured_output",
        "app.infrastructure.ai.prompting.output_contract",
    ):
        assert name in modules, name
