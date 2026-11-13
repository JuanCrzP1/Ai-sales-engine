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

from app.domain.business_config.payment_catalog import SLOTS, data_format

# `link` es el enlace de pago; los demás, los formatos de los medios (`payment_catalog.FORMATS`).
PaymentKind = Literal["link", "mobile", "phone", "account", "clabe", "iban", "email", "reference"]

SECRET_STORE_SOURCE = "secret_store"
SENSITIVE_TRANSFER_FIELDS = SLOTS
REDACTED_PAYMENT_VALUE = "[dato de pago]"
# Valores más cortos no se redactan para no alterar palabras comunes del texto.
MIN_REDACTABLE_CHARS = 4

_MOBILE = re.compile(r"3[0-9]{9}")
_ACCOUNT = re.compile(r"[0-9]{6,20}")
_PHONE = re.compile(r"\+?[0-9]{7,15}")
_EMAIL = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_IBAN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")
# Lo que se ignora al validar y guardar un número: espacios, guiones y puntos.
_SEPARATORS = re.compile(r"[\s.-]+")

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
            for slot in SLOTS:
                if method.get(slot):
                    kind = data_format(str(method.get("type") or ""), slot)
                    yield PaymentField(f"payments.{index}.transfer_methods.{position}.{slot}", kind, method[slot]["secret_ref"])  # type: ignore[arg-type]


def _is_web_address(value: str) -> bool:
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return False
    return parts.scheme in {"http", "https"} and bool(parts.netloc) and not re.search(r"\s", parts.netloc)


def _clabe_ok(digits: str) -> bool:
    """La CLABE mexicana: 18 dígitos y el último es su dígito de control."""
    if not re.fullmatch(r"[0-9]{18}", digits):
        return False
    total = sum((int(digit) * weight) % 10 for digit, weight in zip(digits[:17], [3, 7, 1] * 6))
    return (10 - total % 10) % 10 == int(digits[17])


def _iban_ok(compact: str) -> bool:
    """El IBAN: país, dígitos de control y cuenta; se comprueba con el módulo 97, como lo hacen los bancos."""
    if not _IBAN.fullmatch(compact):
        return False
    rearranged = compact[4:] + compact[:4]
    return int("".join(str(int(char, 36)) for char in rearranged)) % 97 == 1


def normalize_payment_value(kind: str, value: str) -> str:
    """El dato como se guarda: sin espacios sobrantes; los números sin separadores y el IBAN en mayúsculas."""
    text = str(value or "").strip()
    if kind in ("mobile", "phone", "account", "clabe"):
        return _SEPARATORS.sub("", text)
    if kind == "iban":
        return re.sub(r"\s+", "", text).upper()
    return text


def payment_value_problem(kind: PaymentKind, value: str) -> str | None:
    """El motivo por el que un valor no sirve para ese tipo de dato; None si sirve. El mensaje no repite el valor."""
    if kind == "link":
        return None if _is_web_address(value) else "El enlace debe ser una dirección web válida (https://…)."
    clean = normalize_payment_value(kind, value)
    if kind == "mobile":
        return None if _MOBILE.fullmatch(clean) else "Escribe un celular de 10 dígitos que empiece por 3."
    if kind == "phone":
        return None if _PHONE.fullmatch(clean) else "Escribe el número de celular: solo dígitos, con o sin el código del país."
    if kind == "account":
        return None if _ACCOUNT.fullmatch(clean) else "Escribe un número de cuenta válido (solo dígitos)."
    if kind == "clabe":
        return None if _clabe_ok(clean) else "Revisa la CLABE: son 18 dígitos y el último debe coincidir (cópiala de tu banco)."
    if kind == "iban":
        return None if _iban_ok(clean) else "Revisa el IBAN: empieza por el país (ES, DE…) y debe copiarse completo de tu banco."
    if kind == "email":
        return None if _EMAIL.fullmatch(clean) and len(clean) <= 200 else "Escribe un correo válido, por ejemplo pagos@tunegocio.com."
    return None if clean else "Escribe el dato para pagar (tu llave, alias o número)."


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
    if kind in ("reference", "email"):
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
    return redact_values(text, payment_values(runtime_yaml))


# Un número largo en un mensaje: un celular, una cuenta o una referencia (7 cifras o más, con espacios o guiones entre ellas). Los
# precios no entran: llevan puntos o comas («1.320.000») o una moneda al lado.
_LONG_NUMBER = re.compile(r"(?<![\d.,$])\+?\d(?:[ -]?\d){6,}(?![.,]?\d)")
_DIGIT_RUN = re.compile(r"\d(?:[ .\-]?\d)+")
_MONEY_BEFORE = re.compile(r"(\$|\b(cop|usd|mxn|pen|eur|clp|ars|s/)\.?)\s*$", re.IGNORECASE)
_MONEY_AFTER = re.compile(r"^\s*(pesos|d[oó]lares|soles|euros|cop|usd|mxn|pen|eur|clp|ars)\b", re.IGNORECASE)
_SHORTEST_LONG_NUMBER = 7
# Un número conocido puede ir con el indicativo del país delante («+57 300…»).
_LONGEST_PREFIX = 3


def mask_invented_numbers(text: str, known: str) -> str:
    """Cambia por «[dato de pago]» cada número largo que la IA escribió sin haberlo leído en ninguna parte (`known`: el negocio y la
    conversación). La IA no ve los datos de pago; un celular o una cuenta que aparece en su mensaje y no estaba en lo que leyó es
    inventado, y un cliente podría pagar ahí. Con el marcador, el sistema pone el dato real (`payment_delivery.py`)."""
    message = str(text or "")
    if not _LONG_NUMBER.search(message):
        return message
    known_runs = {digits for run in _DIGIT_RUN.findall(str(known or "")) if len(digits := re.sub(r"\D", "", run)) >= _SHORTEST_LONG_NUMBER}

    def _is_known(digits: str) -> bool:
        return any(digits in run or (run in digits and len(digits) - len(run) <= _LONGEST_PREFIX) for run in known_runs)

    def _replace(match: re.Match) -> str:
        before, after = message[max(0, match.start() - 8):match.start()], message[match.end():match.end() + 12]
        if _is_known(re.sub(r"\D", "", match.group(0))) or _MONEY_BEFORE.search(before) or _MONEY_AFTER.search(after):
            return match.group(0)
        return REDACTED_PAYMENT_VALUE

    return _LONG_NUMBER.sub(_replace, message)


# Un marcador que escribe la IA por su cuenta para un dato que no ve: «[número de Nequi]», «[link de pago]», «[datos de la cuenta]».
_OWN_MARKER = re.compile(r"\[[^\[\]\n]{0,40}\b(n[uú]mero|datos?|cuenta|link|enlace|llave|clabe|iban)\b[^\[\]\n]{0,40}\]", re.IGNORECASE)


def mask_own_markers(text: str) -> str:
    """Cambia por «[dato de pago]» los marcadores que la IA escribe por su cuenta («[número de Nequi]»): son el mismo aviso de que ahí
    va un dato que ella no ve, y nunca deben llegarle al cliente."""
    return _OWN_MARKER.sub(REDACTED_PAYMENT_VALUE, str(text or ""))


def redact_values(text: str, values: list[str] | tuple[str, ...]) -> str:
    """Cambia cada valor (de los que tienen al menos `MIN_REDACTABLE_CHARS`) por «[dato de pago]», del más largo al más corto
    para que uno que contiene a otro se oculte entero."""
    chosen = sorted({value.strip() for value in values if len(value.strip()) >= MIN_REDACTABLE_CHARS}, key=len, reverse=True)
    for value in chosen:
        text = text.replace(value, REDACTED_PAYMENT_VALUE)
    return text
