"""Respuestas rápidas: mensajes guardados del negocio que el equipo pone en un chat sin copiar y pegar.

Cada una tiene un **atajo** («precios», se busca escribiendo «/precios»), una **categoría** opcional («Precios», «Pagos»…) y de uno a
diez **mensajes** que salen en orden. En los textos, `{nombre}` se cambia por el primer nombre del cliente al usarla. Por ahora cada
mensaje es un texto: los archivos llegarán cuando el chat del panel pueda enviarlos.

Se organizan en Configuración → Respuestas rápidas y en el chat solo se buscan y se envían (como en Intercom o Zendesk).

Todo aquí es puro: valida y normaliza, sin base de datos ni red.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

MAX_QUICK_REPLIES = 500
MAX_PIECES = 10
MAX_TEXT_CHARS = 4000  # lo mismo que admite una respuesta del equipo (`conversations.MAX_REPLY_CHARS`)
MAX_CATEGORY_CHARS = 40
# Minúsculas sin tildes, números, espacios, guiones y guiones bajos; hasta 40.
SHORTCUT = re.compile(r"^[a-z0-9_-][a-z0-9 _-]{0,39}$")
NAME_PLACEHOLDER = "{nombre}"


@dataclass(frozen=True)
class QuickReplyDraft:
    """Lo que escribe el negocio, ya validado."""

    shortcut: str
    category: str | None
    pieces: tuple[str, ...]


@dataclass(frozen=True)
class QuickReply:
    id: str
    shortcut: str
    category: str | None
    pieces: tuple[str, ...]
    use_count: int
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


def normalize_shortcut(value: str) -> str:
    """El atajo como se guarda: «/Saludo Inicial » → «saludo inicial»; «Crédito» → «credito»."""
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn").lower().strip()
    text = re.sub(r"^[#/]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_category(value: str) -> str:
    """Sin espacios de más y con la primera letra en mayúscula: « precios » → «Precios»."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:1].upper() + text[1:]


def validated(*, shortcut: Any, category: Any = None, pieces: Any) -> QuickReplyDraft:
    """Valida lo que llega del panel o de un agente. Los problemas vuelven por campo, con la ruta que muestra el panel."""
    issues: list[FieldIssue] = []

    clean_shortcut = normalize_shortcut(shortcut) if isinstance(shortcut, str) else ""
    if not clean_shortcut:
        issues.append(FieldIssue("shortcut", "Escribe el atajo, por ejemplo «precios»."))
    elif not SHORTCUT.fullmatch(clean_shortcut):
        issues.append(FieldIssue("shortcut", "El atajo admite hasta 40 letras sin tildes, números, espacios, guiones y guiones bajos."))

    clean_category: str | None = None
    if category is not None and not isinstance(category, str):
        issues.append(FieldIssue("category", "La categoría no es válida."))
    elif category is not None:
        clean_category = normalize_category(category) or None
        if clean_category and len(clean_category) > MAX_CATEGORY_CHARS:
            issues.append(FieldIssue("category", f"La categoría admite hasta {MAX_CATEGORY_CHARS} caracteres."))

    clean_pieces: list[str] = []
    if not isinstance(pieces, list) or not pieces:
        issues.append(FieldIssue("pieces", "Escribe al menos un mensaje."))
    elif len(pieces) > MAX_PIECES:
        issues.append(FieldIssue("pieces", f"Una respuesta rápida admite hasta {MAX_PIECES} mensajes."))
    else:
        for index, piece in enumerate(pieces):
            text = piece.get("text") if isinstance(piece, dict) and piece.get("kind", "text") == "text" else piece if isinstance(piece, str) else None
            text = text.strip() if isinstance(text, str) else ""
            if not text:
                issues.append(FieldIssue(f"pieces[{index}].text", f"El mensaje {index + 1} está vacío: escríbelo o quítalo."))
            elif len(text) > MAX_TEXT_CHARS:
                issues.append(FieldIssue(f"pieces[{index}].text", f"El mensaje {index + 1} admite hasta {MAX_TEXT_CHARS} caracteres."))
            else:
                clean_pieces.append(text)

    if issues:
        raise InvalidFieldsError("Revisa la respuesta rápida.", issues)
    return QuickReplyDraft(shortcut=clean_shortcut, category=clean_category, pieces=tuple(clean_pieces))


def first_name(name: str | None) -> str:
    """El primer nombre del cliente: «maría fernanda gómez» → «María». Sin nombre, vacío."""
    word = str(name or "").strip().split(" ")[0] if str(name or "").strip() else ""
    return word[:1].upper() + word[1:].lower() if word else ""


def fill_name(text: str, name: str | None) -> str:
    """Cambia `{nombre}` por el primer nombre del cliente. Sin nombre, lo quita junto con el espacio de antes («Hola {nombre},» → «Hola,»)."""
    value = first_name(name)
    if value:
        return text.replace(NAME_PLACEHOLDER, value)
    return re.sub(r"[ \t]*\{nombre\}", "", text)
