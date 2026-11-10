"""Qué entradas de una lista van al prompt cuando no caben todas: las que más palabras comparten con lo que pregunta el cliente.

Lo usan las preguntas frecuentes, el catálogo y la estrategia avanzada, para que un negocio con muchas entradas no infle cada mensaje.
Si todo cabe, va todo; si no, se eligen por relevancia hasta llenar el espacio y se escriben siempre en el orden del negocio.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")

# Palabras que no distinguen una entrada de otra.
STOPWORDS = frozenset(
    "a al como con cual cuales cuando de del donde el en es esta este hay la las le les lo los me mi mis no o para por que se si sin "
    "su sus te tu tus un una uno unos unas y ya".split()
)


def _stem(word: str) -> str:
    """Singular aproximado: «domingos» y «domingo» cuentan como la misma palabra."""
    if len(word) > 4 and word.endswith("es"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def words(text: str) -> set[str]:
    plain = "".join(char for char in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(char))
    return {_stem(word) for word in re.findall(r"[a-z0-9]+", plain) if word not in STOPWORDS}


def grouped_lines(entries: Sequence[tuple[str | None, str]], *, query: str, max_chars: int) -> list[str]:
    """Las líneas de una capa que caben: cada entrada es (título del grupo o None, texto). Las elegidas se escriben bajo su título,
    como viñetas, en el orden del negocio; un título sin entradas elegidas no se escribe."""
    # El título cuenta para la relevancia: «Si duda por el precio» acerca todas sus líneas a un cliente que habla del precio.
    shown = select(entries, size=lambda entry: len(entry[1]) + 3 + len(entry[0] or ""), text=lambda entry: f"{entry[0] or ''} {entry[1]}",
                   query=query, max_chars=max_chars)
    lines: list[str] = []
    current: str | None = None
    for title, text in shown:
        if title is None:
            lines.append(text)
            continue
        if title != current:
            lines.append(title)
            current = title
        lines.append(f"- {text}")
    return lines


def select(entries: Sequence[T], *, size: Callable[[T], int], text: Callable[[T], str], query: str, max_chars: int) -> list[T]:
    """Las entradas que caben en `max_chars`, primero las más relacionadas con `query`, en el orden original."""
    sizes = [size(entry) for entry in entries]
    if sum(sizes) <= max_chars:
        return list(entries)
    asked = words(query)
    by_relevance = sorted(range(len(entries)), key=lambda index: (-len(asked & words(text(entries[index]))), index))
    chosen: set[int] = set()
    used = 0
    for index in by_relevance:
        if used + sizes[index] <= max_chars:
            chosen.add(index)
            used += sizes[index]
    return [entry for index, entry in enumerate(entries) if index in chosen]
