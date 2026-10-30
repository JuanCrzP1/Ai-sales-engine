"""Resolución de los datos de pago sensibles referenciados desde el contrato (`SecretRef`).

Orígenes (`<origen>:<clave>`):
- `legacy_yaml`: lee el valor en su posición original de los YAML del mismo negocio
  (p. ej. `legacy_yaml:pricing.plans.0.payment.link`). Puente temporal para los negocios migrados.
- `secret_store`: valor cifrado en la base de datos (`payment_secret_store.py`).

`resolve_by_source` combina resolutores para que un mismo documento use ambos orígenes.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.domain.business_config.contract import SecretRef
from app.infrastructure.config.legacy_yaml_importer import LEGACY_SECRET_SOURCE


class SecretResolutionError(LookupError):
    pass


def _walk(data: Any, path: str) -> Any:
    node = data
    for token in path.split("."):
        if isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        elif isinstance(node, dict) and token in node:
            node = node[token]
        else:
            raise SecretResolutionError(f"ruta de secreto inexistente: {path}")
    if isinstance(node, (dict, list)) or node is None:
        raise SecretResolutionError(f"la ruta de secreto no apunta a un valor: {path}")
    return node


class LegacyYamlSecretResolver:
    """Resuelve referencias `legacy_yaml:` contra las secciones YAML de un único negocio."""

    def __init__(self, load_sections: Callable[[], dict[str, dict]]) -> None:
        self._load_sections = load_sections
        self._sections: dict[str, dict] | None = None

    def __call__(self, ref: SecretRef) -> str:
        source, _, path = ref.secret_ref.partition(":")
        if source != LEGACY_SECRET_SOURCE:
            raise SecretResolutionError(f"origen de secreto no soportado: {source}")
        if self._sections is None:
            self._sections = self._load_sections()
        value = _walk(self._sections, path)
        return value if isinstance(value, str) else str(value)


def resolve_by_source(resolvers: Mapping[str, Callable[[SecretRef], str]]) -> Callable[[SecretRef], str]:
    """Delega cada referencia en el resolutor de su origen; un origen desconocido es un error."""

    def _resolve(ref: SecretRef) -> str:
        source = ref.secret_ref.partition(":")[0]
        if source not in resolvers:
            raise SecretResolutionError(f"origen de secreto no soportado: {source}")
        return resolvers[source](ref)

    return _resolve
