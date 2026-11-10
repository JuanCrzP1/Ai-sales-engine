"""Utilidades de texto del prompt: valores del runtime convertidos a texto limpio, sin decidir nada del negocio."""
from __future__ import annotations

from collections.abc import Iterable

_SENTENCE_ENDINGS = (".", "!", "?", "…")


def as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def dicts(value: object) -> list[dict]:
    return [item for item in as_list(value) if isinstance(item, dict)]


def as_text(value: object) -> str:
    """Texto, número o booleano como texto; cualquier otra cosa (listas, objetos, None) como vacío."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value).strip()
    return ""


def texts(value: object) -> list[str]:
    """Los textos no vacíos de una lista."""
    return [text for item in as_list(value) if (text := as_text(item))]


def one_line(value: object) -> str:
    return " ".join(as_text(value).split())


def bounded_text(value: object, *, max_chars: int) -> str:
    """El texto completo en una línea. Lo que viene del contrato ya respeta `max_chars`; si algo lo supera, se corta en una palabra."""
    text = one_line(value)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0]


def sentence(text: str) -> str:
    """Termina en punto, sin duplicarlo si el texto ya cierra la frase."""
    text = text.strip()
    return text if not text or text.endswith(_SENTENCE_ENDINGS) else f"{text}."


def readable(identifier: str) -> str:
    """`tomar_pedido` → `tomar pedido`: los identificadores del panel, legibles para la IA."""
    return identifier.replace("_", " ").strip()


def dedupe(values: Iterable[str]) -> list[str]:
    """Sin vacíos ni repetidos, en el orden en que llegan."""
    ordered: list[str] = []
    for value in values:
        if value and value not in ordered:
            ordered.append(value)
    return ordered


def section(header: str, lines: Iterable[str]) -> str:
    """Un encabezado y sus líneas; "" si no hay ninguna."""
    body = [line for line in lines if line]
    return "\n".join([header, *body]) if body else ""


def bullets(items: Iterable[str]) -> list[str]:
    return [f"- {item}" for item in items if item]
