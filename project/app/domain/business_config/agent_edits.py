"""Cómo un agente de IA (MCP) cambia la configuración de un negocio: por partes y sin tocar lo que no pidió.

- `merged`: aplica un cambio parcial sobre el documento. Los objetos se combinan clave por clave; una lista se reemplaza entera
  (así se agrega, quita u ordena sin ambigüedad) y `null` quita el dato.
- `with_new_payment_values`: donde el agente escribió `{"value": "3001234567"}` en lugar de una referencia, pone una referencia
  nueva y separa el valor para guardarlo cifrado, como hace el panel. El valor nunca vuelve al agente.
- `business_slug_for`: un identificador válido y libre a partir del nombre del negocio.

Todo aquí es puro: el servicio sigue siendo la autoridad (valida el contrato y el formato de cada dato de pago al guardar).
"""
from __future__ import annotations

import copy
import re
import unicodedata
import uuid
from collections.abc import Callable, Iterable
from typing import Any

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError
from app.domain.business_config.payment_data import SECRET_STORE_SOURCE

MAX_SLUG_CHARS = 40
_PAYMENT_HOLDERS = ("link", "number", "account_number", "reference")


def merged(document: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """El documento con los cambios aplicados: objetos combinados, listas reemplazadas y `null` para quitar."""

    def apply(base: Any, patch: Any) -> Any:
        if not isinstance(patch, dict) or not isinstance(base, dict):
            return copy.deepcopy(patch)
        result = copy.deepcopy(base)
        for key, value in patch.items():
            if value is None:
                result.pop(key, None)
            else:
                result[key] = apply(result.get(key), value)
        return result

    return apply(document, changes)


def _new_ref(profile_id: str, field: str, new_id: Callable[[], str]) -> str:
    return f"{SECRET_STORE_SOURCE}:{profile_id}.{field}.agente_{new_id()}"


def with_new_payment_values(document: dict[str, Any], new_id: Callable[[], str] = lambda: uuid.uuid4().hex[:12]) -> tuple[dict[str, Any], dict[str, str]]:
    """El documento con referencias en lugar de los valores que escribió el agente, y esos valores por su referencia nueva.

    Un dato de pago solo puede ir donde el contrato lo espera (el enlace del perfil y el número, la cuenta o la referencia de un
    medio de transferencia). Un `{"value": ...}` en otro lugar es un error: así ningún valor termina guardado en claro."""
    result = copy.deepcopy(document)
    values: dict[str, str] = {}
    issues: list[FieldIssue] = []
    for index, profile in enumerate(result.get("payments") or []):
        if not isinstance(profile, dict):
            continue
        profile_id = str(profile.get("id") or f"perfil_{index}")
        holders: list[tuple[dict[str, Any], str, str]] = [(profile, "link", f"payments.{index}.link")]
        for position, method in enumerate(profile.get("transfer_methods") or []):
            if isinstance(method, dict):
                for name in _PAYMENT_HOLDERS[1:]:
                    holders.append((method, name, f"payments.{index}.transfer_methods.{position}.{name}"))
        for owner, name, path in holders:
            holder = owner.get(name)
            if not isinstance(holder, dict) or "value" not in holder:
                continue
            value = str(holder.get("value") or "").strip()
            if not value:
                issues.append(FieldIssue(path, "Escribe el dato de pago o quítalo."))
                continue
            field = name if name == "link" else f"{owner.get('type') or 'medio'}.{name}"
            ref = _new_ref(profile_id, field, new_id)
            owner[name] = {"secret_ref": ref}
            values[ref] = value
    stray = [path for path in _value_paths(result)]
    issues.extend(FieldIssue(path, "Un dato de pago solo va en el enlace o en el número, la cuenta o la referencia de un medio de pago.") for path in stray)
    if issues:
        raise InvalidFieldsError("Revisa los datos de pago.", issues)
    return result, values


def _value_paths(node: Any, path: str = "") -> Iterable[str]:
    """Dónde quedó un `{"value": ...}` que no se convirtió en referencia."""
    if isinstance(node, dict):
        if "value" in node and len(node) == 1:
            yield path or "documento"
            return
        for key, value in node.items():
            yield from _value_paths(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _value_paths(value, f"{path}.{index}")


def business_slug_for(name: str, taken: Iterable[str]) -> str:
    """Un identificador válido (minúsculas, números y guion bajo) a partir del nombre, sin repetir uno que ya exista."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    base = re.sub(r"[^a-z0-9]+", "_", plain).strip("_")[:MAX_SLUG_CHARS].strip("_") or "negocio"
    if not base[0].isalnum():
        base = f"negocio_{base}"
    used = set(taken)
    candidate, counter = base, 2
    while candidate in used:
        suffix = f"_{counter}"
        candidate = f"{base[: MAX_SLUG_CHARS - len(suffix)]}{suffix}"
        counter += 1
    return candidate
