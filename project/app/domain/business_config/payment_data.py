"""Datos de pago sensibles: links, números, cuentas y referencias.

Define qué valores son sensibles según el contrato (los que se guardan como `SecretRef`), dónde están en un documento,
qué formato deben tener y cómo se enmascaran para reconocerlos. El panel avisa con las mismas reglas mientras se escribe,
pero la autoridad es esta: el servidor las aplica antes de guardar, venga la petición de donde venga.

El motor usa `redact_payment_values` para que estos valores nunca lleguen a la IA (todo el prompt, incluido el historial)
ni al registro `conversation_trace`; el cliente los recibe cuando elige el método. Ver `tests/test_payment_data_protection.py`.
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlsplit

PaymentKind = Literal["link", "mobile", "account", "reference"]

SECRET_STORE_SOURCE = "secret_store"
_TRANSFER_FIELD_KINDS: dict[str, PaymentKind] = {"number": "mobile", "account_number": "account", "reference": "reference"}
SENSITIVE_TRANSFER_FIELDS = tuple(_TRANSFER_FIELD_KINDS)
REDACTED_PAYMENT_VALUE = "[dato de pago]"
# Valores más cortos no se redactan para no alterar palabras comunes del texto.
MIN_REDACTABLE_CHARS = 4

_MOBILE = re.compile(r"3[0-9]{9}")
_ACCOUNT = re.compile(r"[0-9]{6,20}")

MASK = "••••"
# Un valor más corto se oculta entero: unos pocos caracteres ya dirían demasiado.
_SHORTEST_WITH_VISIBLE_END = 6


@dataclass(frozen=True)
class PaymentField:
    """Un dato de pago dentro de un documento, con la ruta y el tipo que determinan cómo se escribe."""

    path: str
    kind: PaymentKind
    ref: str


def iter_secret_refs(document: Any) -> Iterator[dict]:
    """Objetos `{"secret_ref": ...}` de un documento del contrato, para leerlos o reemplazarlos."""
    if isinstance(document, dict):
        if isinstance(document.get("secret_ref"), str):
            yield document
        for value in document.values():
            yield from iter_secret_refs(value)
    elif isinstance(document, list):
        for value in document:
            yield from iter_secret_refs(value)


def iter_payment_fields(document: dict) -> Iterator[PaymentField]:
    """Los datos de pago de un documento ya validado contra el contrato."""
    for index, profile in enumerate(document.get("payments") or []):
        if profile.get("link"):
            yield PaymentField(f"payments.{index}.link", "link", profile["link"]["secret_ref"])
        for position, method in enumerate(profile.get("transfer_methods") or []):
            for name, kind in _TRANSFER_FIELD_KINDS.items():
                if method.get(name):
                    yield PaymentField(f"payments.{index}.transfer_methods.{position}.{name}", kind, method[name]["secret_ref"])


def _is_web_address(value: str) -> bool:
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return False
    return parts.scheme in {"http", "https"} and bool(parts.netloc) and not re.search(r"\s", parts.netloc)


def payment_value_problem(kind: PaymentKind, value: str) -> str | None:
    """El motivo por el que un valor no sirve para ese tipo de dato; None si sirve. El mensaje no repite el valor."""
    if kind == "link":
        return None if _is_web_address(value) else "El enlace debe ser una dirección web válida (https://…)."
    if kind == "mobile":
        return None if _MOBILE.fullmatch(re.sub(r"\s+", "", value)) else "Escribe un celular de 10 dígitos que empiece por 3."
    if kind == "account":
        return None if _ACCOUNT.fullmatch(re.sub(r"[\s-]+", "", value)) else "Escribe un número de cuenta válido (solo dígitos)."
    return None if value.strip() else "Escribe tu llave o referencia Bre-B."


def _masked_end(value: str, visible: int) -> str:
    """Solo el final, sin revelar nunca la mitad del valor ni su longitud."""
    if len(value) < _SHORTEST_WITH_VISIBLE_END:
        return MASK
    return MASK + value[-min(visible, (len(value) - 1) // 2) :]


def _masked_link(value: str) -> str:
    """Su servidor identifica al proveedor. La ruta y los parámetros pueden llevar códigos propios del negocio: no salen."""
    try:
        parts = urlsplit(value)
        host = parts.hostname
    except ValueError:
        return MASK
    if not host:
        return MASK
    if parts.path.strip("/") or parts.query or parts.fragment:
        return f"{parts.scheme}://{host}/{MASK}"
    # Sin nada que ocultar después del servidor, se oculta parte de este: el valor nunca sale completo.
    _first, _dot, rest = host.partition(".")
    return f"{parts.scheme}://{MASK}.{rest}" if rest else MASK


def mask_payment_value(kind: PaymentKind, value: str) -> str:
    """Lo único que sale del servidor de un dato de pago guardado: lo justo para reconocerlo."""
    text = value.strip()
    if kind == "link":
        return _masked_link(text)
    if kind == "reference":
        return _masked_end(text, 3)
    return _masked_end(re.sub(r"[\s-]+", "", text), 4)


def iter_payment_blocks(pricing: dict) -> list[dict]:
    """Bloques `payment` de los planes, del catálogo y de la raíz de `pricing`, en ese orden."""
    blocks: list[dict] = []
    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        payment = plan.get("payment") if isinstance(plan.get("payment"), dict) else {}
        if payment:
            blocks.append(payment)

    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    catalog_payment = catalog.get("payment") if isinstance(catalog.get("payment"), dict) else {}
    if catalog_payment:
        blocks.append(catalog_payment)

    root_payment = pricing.get("payment") if isinstance(pricing.get("payment"), dict) else {}
    if root_payment:
        blocks.append(root_payment)

    return blocks


def payment_values(runtime_yaml: dict) -> list[str]:
    """Valores sensibles configurados (incluidos los de métodos desactivados), del más largo al más corto."""
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml, dict) and isinstance(runtime_yaml.get("pricing"), dict) else {}
    values: set[str] = set()
    for block in iter_payment_blocks(pricing):
        values.add(str(block.get("link") or "").strip())
        transfer = block.get("transfer") if isinstance(block.get("transfer"), dict) else {}
        methods = transfer.get("methods") if isinstance(transfer.get("methods"), list) else []
        for method in methods:
            if isinstance(method, dict):
                values.update(str(method.get(field) or "").strip() for field in SENSITIVE_TRANSFER_FIELDS)
    return sorted((value for value in values if len(value) >= MIN_REDACTABLE_CHARS), key=len, reverse=True)


def redact_payment_values(text: str, runtime_yaml: dict) -> str:
    for value in payment_values(runtime_yaml):
        text = text.replace(value, REDACTED_PAYMENT_VALUE)
    return text
