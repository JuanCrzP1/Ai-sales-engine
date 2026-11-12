"""Los problemas de validación del contrato, por campo y en español, a partir de los errores de pydantic.

Nunca repiten el valor recibido (podría ser un dato de pago). Los usan la API del panel y el servidor MCP: el agente recibe además
las opciones permitidas cuando eligió una que no existe, para corregirse solo.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

# Pydantic añade al recorrido las ramas de los tipos compuestos (`int`, `float`, `function-after[...]`...).
_UNION_BRANCHES = {"int", "float", "str", "bool"}
_TECHNICAL_MESSAGES = {
    "model=plans requiere al menos un plan y ningún catálogo": "Agrega al menos un plan o servicio.",
    "model=catalog requiere un catálogo y ningún plan": "Agrega al menos un producto al catálogo.",
}


def _is_branch(part: Any) -> bool:
    return isinstance(part, str) and (part in _UNION_BRANCHES or "[" in part or part.startswith("constrained-"))


def issue_path(location: Iterable[Any]) -> str:
    return ".".join(str(part) for part in location if not _is_branch(part))


def issue_message(error: dict[str, Any]) -> str:
    kind = error["type"]
    context = error.get("ctx") or {}
    if kind == "value_error":
        text = re.sub(r"^Value error, ", "", error["msg"])
        return _TECHNICAL_MESSAGES.get(text, text[:1].upper() + text[1:] + ("" if text.endswith(".") else "."))
    if kind == "missing":
        return "Este dato es obligatorio."
    if kind == "string_too_long":
        return f"Admite hasta {context.get('max_length')} caracteres."
    if kind == "too_long":
        return f"Admite hasta {context.get('max_length')} elementos."
    if kind == "too_short":
        return f"Necesita al menos {context.get('min_length')} elemento."
    if kind == "string_pattern_mismatch":
        return "El formato no es válido."
    if kind in {"greater_than_equal", "greater_than"}:
        return f"Debe ser {context.get('ge', context.get('gt'))} o más."
    if kind in {"literal_error", "enum"}:
        return "Elige una de las opciones permitidas."
    if kind == "extra_forbidden":
        return "Este dato no forma parte de la configuración."
    if kind.startswith(("date_", "datetime_")):
        return "Escribe una fecha válida."
    return "El valor no tiene el tipo esperado."


def validation_issues(errors: Iterable[dict[str, Any]], *, with_options: bool = False) -> list[dict[str, str]]:
    """Un problema por campo, con su ruta en el documento. Sin `input`: podría ser un dato de pago. Con `with_options`, las
    opciones permitidas de una lista cerrada (para un agente que debe corregir el valor)."""
    issues: dict[str, dict[str, str]] = {}
    for error in errors:
        path = issue_path(error["loc"])
        if path in issues:
            continue
        issue = {"path": path, "message": issue_message(error)}
        expected = (error.get("ctx") or {}).get("expected")
        if with_options and error["type"] in {"literal_error", "enum"} and expected:
            issue["options"] = str(expected)
        issues[path] = issue
    return list(issues.values())
