"""Los medios de pago que un negocio puede configurar, de cualquier país: una sola fuente para el contrato, el panel y el motor.

Cada medio dice cómo se llama, de qué país es, qué dato pide (y dónde se guarda, siempre cifrado), cómo se valida ese dato, cómo
sale en el mensaje al cliente y cómo lo nombra un cliente en el chat. El panel recibe este catálogo generado en
`apps/admin-web/src/contracts/businessConfig.v1.ts` (`scripts/generate_business_config_types.py`): nadie lo copia a mano.

- Lo que se paga va en una de tres casillas cifradas del contrato (`number`, `account_number`, `reference`). Los medios que ya
  existían (Nequi, Daviplata, cuenta bancaria, Bre-B) siguen exactamente donde estaban: ningún negocio pierde ni mueve datos.
- «Otro medio» (`custom`) es libre: el negocio le pone el nombre y dice cómo se llama su dato («Alias», «Número»).
- «Efectivo o contraentrega» (`cash`) no pide datos: el cliente recibe la instrucción del negocio.
- La IA solo ve el nombre del medio. El dato real lo envía el sistema (`application/pipeline/payment_delivery.py`).
"""
from __future__ import annotations

from dataclasses import dataclass

# Dónde se guarda el dato de un medio (las tres casillas cifradas del contrato).
SLOTS: tuple[str, ...] = ("number", "account_number", "reference")
# Cómo se valida cada dato (`payment_data.payment_value_problem`): `mobile` es un celular de Colombia, `phone` uno de cualquier
# país, `reference` cualquier dato no vacío (una llave, un alias).
FORMATS: tuple[str, ...] = ("mobile", "phone", "account", "clabe", "iban", "email", "reference")


@dataclass(frozen=True)
class DataField:
    """El dato que se paga: dónde se guarda, cómo se pregunta en el panel, cómo se valida y cómo sale en el mensaje."""

    slot: str
    label: str
    format: str
    placeholder: str = ""
    # Cómo sale en el mensaje al cliente; `{value}` es el dato real.
    shown_as: str = "{value}"


@dataclass(frozen=True)
class PaymentMethodKind:
    id: str
    name: str
    group: str
    data: DataField | None
    # Cómo lo nombra un cliente en el chat (expresión regular, en minúsculas).
    aliases: str
    # Pide el banco y el tipo de cuenta (cuenta bancaria).
    needs_bank: bool = False
    # El negocio le pone el nombre y dice cómo se llama su dato.
    custom: bool = False


COLOMBIA, MEXICO, PERU, ARGENTINA, SPAIN, USA, ANYWHERE = "Colombia", "México", "Perú", "Argentina", "España", "Estados Unidos", "Todos los países"
GROUPS: tuple[str, ...] = (COLOMBIA, MEXICO, PERU, ARGENTINA, SPAIN, USA, ANYWHERE)

_MOBILE_CO = DataField("number", "Número de celular", "mobile", "3001234567")

PAYMENT_METHODS: tuple[PaymentMethodKind, ...] = (
    PaymentMethodKind("nequi", "Nequi", COLOMBIA, _MOBILE_CO, r"\bnequi\b"),
    PaymentMethodKind("daviplata", "Daviplata", COLOMBIA, _MOBILE_CO, r"\bdaviplata\b"),
    PaymentMethodKind(
        "bank", "Cuenta bancaria", ANYWHERE, DataField("account_number", "Número de cuenta", "account", "1234567890"),
        r"\bbanco\b|\bbancaria\b|\bcuenta de ahorros\b|\bcuenta corriente\b|\bbancolombia\b", needs_bank=True,
    ),
    PaymentMethodKind("breb", "Bre-B", COLOMBIA, DataField("reference", "Llave o referencia Bre-B", "reference", "@tunegocio", "Llave: {value}"), r"\bbre-?b\b|\bllave\b"),
    PaymentMethodKind("spei", "Transferencia SPEI", MEXICO, DataField("reference", "CLABE interbancaria", "clabe", "032180000118359719", "CLABE: {value}"), r"\bspei\b|\bclabe\b"),
    PaymentMethodKind("oxxo", "Depósito en OXXO", MEXICO, DataField("reference", "Número de tarjeta para depositar", "account", "4152313412345678", "Tarjeta: {value}"), r"\boxxo\b"),
    PaymentMethodKind("yape", "Yape", PERU, DataField("number", "Número de celular", "phone", "987654321"), r"\byape\b"),
    PaymentMethodKind("plin", "Plin", PERU, DataField("number", "Número de celular", "phone", "987654321"), r"\bplin\b"),
    PaymentMethodKind("mercadopago", "Mercado Pago", ARGENTINA, DataField("reference", "Alias o CVU", "reference", "tunegocio.mp", "Alias/CVU: {value}"), r"\bmercado ?pago\b|\bcvu\b|\balias\b"),
    PaymentMethodKind("bizum", "Bizum", SPAIN, DataField("number", "Número de móvil", "phone", "612345678"), r"\bbizum\b"),
    PaymentMethodKind("iban", "Transferencia (IBAN)", SPAIN, DataField("account_number", "IBAN", "iban", "ES91 2100 0418 4502 0005 1332", "IBAN: {value}"), r"\biban\b|\bsepa\b"),
    PaymentMethodKind("zelle", "Zelle", USA, DataField("reference", "Correo o celular de Zelle", "reference", "pagos@tunegocio.com"), r"\bzelle\b"),
    PaymentMethodKind("paypal", "PayPal", ANYWHERE, DataField("reference", "Correo de PayPal", "email", "pagos@tunegocio.com"), r"\bpay ?pal\b"),
    PaymentMethodKind("cash", "Efectivo o contraentrega", ANYWHERE, None, r"\befectivo\b|\bcontra ?entrega\b|\bal recibir\b"),
    PaymentMethodKind("custom", "Otro medio", ANYWHERE, DataField("reference", "Dato para pagar", "reference", ""), r"(?!)", custom=True),
)
PAYMENT_METHOD_IDS: tuple[str, ...] = tuple(kind.id for kind in PAYMENT_METHODS)
_BY_ID = {kind.id: kind for kind in PAYMENT_METHODS}
# Lo que sale si el negocio no escribe una instrucción para el efectivo.
DEFAULT_CASH_TEXT = "Pagas en efectivo al recibir tu pedido."


def method_kind(method_id: str) -> PaymentMethodKind | None:
    return _BY_ID.get(str(method_id or "").strip().lower())


def data_format(method_id: str, slot: str) -> str:
    """Cómo se valida el dato guardado en `slot` de un medio. Una casilla que el medio no usa se valida como un dato cualquiera."""
    kind = method_kind(method_id)
    return kind.data.format if kind and kind.data and kind.data.slot == slot else "reference"


def catalog_for_panel() -> list[dict]:
    """El catálogo como lo recibe el panel (generado en su archivo de tipos)."""
    return [
        {
            "id": kind.id,
            "name": kind.name,
            "group": kind.group,
            "data": None if kind.data is None else {
                "slot": kind.data.slot, "label": kind.data.label, "format": kind.data.format, "placeholder": kind.data.placeholder,
                "shownAs": kind.data.shown_as,
            },
            "needsBank": kind.needs_bank,
            "custom": kind.custom,
        }
        for kind in PAYMENT_METHODS
    ]
