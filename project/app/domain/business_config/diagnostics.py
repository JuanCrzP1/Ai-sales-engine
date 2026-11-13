"""Diagnóstico de un BusinessConfig válido: incoherencias y datos incompletos que no bloquean.

La validación del contrato (`contract/`) rechaza los documentos rotos: referencias inexistentes,
valores imposibles, combinaciones contradictorias que ningún negocio puede querer. Lo que aquí se
reporta es distinto: el documento es usable, pero tiene algo que el negocio debería decidir o
completar (p. ej. "cierra por link de pago" sin link configurado). Corregirlo cambia datos del
negocio, por eso no se hace automáticamente.

- `incoherencia`: dos datos del negocio se contradicen.
- `incompleto`: falta un dato que el asistente necesitaría para atender bien.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.domain.business_config.contract import BusinessConfig

DiagnosticKind = Literal["incoherencia", "incompleto"]

# Modalidad de atención → modo de entrega que la hace posible.
SERVICE_MODE_FULFILLMENT = {"domicilio": "delivery", "envio": "shipping", "recoger": "pickup"}
# Datos que pide el cierre (`sales.closing.required_data`) → campo de `capabilities.data_collection`.
REQUIRED_DATA_FIELDS = {"name": "nombre", "phone": "telefono", "address": "direccion"}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    kind: DiagnosticKind
    path: str
    message: str


def review(config: BusinessConfig, *, today: date | None = None) -> list[Diagnostic]:
    """Diagnósticos del documento, en orden estable."""
    today = today or date.today()
    found: list[Diagnostic] = []

    def add(code: str, kind: DiagnosticKind, path: str, message: str) -> None:
        found.append(Diagnostic(code, kind, path, message))

    capabilities = config.capabilities
    if capabilities.closing_methods.payment_link and not any(profile.link and profile.link_enabled is not False for profile in config.payments):
        missing = "un link activo" if any(profile.link for profile in config.payments) else "link"
        add("cierre_por_link_sin_link", "incoherencia", "capabilities.closing_methods.payment_link",
            f"El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene {missing}.")

    referenced = {plan.payment_profile for plan in config.offer.plans or []}
    if config.offer.catalog is not None:
        referenced.add(config.offer.catalog.payment_profile)
    for profile in config.payments:
        if profile.id not in referenced:
            add("perfil_de_pago_sin_uso", "incoherencia", f"payments[id={profile.id}]",
                f"El perfil de pago '{profile.id}' no lo usa ningún plan ni el catálogo.")
        if profile.transfer_enabled and all(method.enabled is False for method in profile.transfer_methods):
            add("transferencias_sin_cuentas_activas", "incoherencia", f"payments[id={profile.id}]",
                f"El perfil de pago '{profile.id}' acepta transferencias, pero todas sus cuentas están inactivas.")

    features = config.features
    if features is not None and features.multi_plan is False and len(config.offer.plans or []) > 1:
        add("multi_plan_contradice_oferta", "incoherencia", "features.multi_plan",
            f"multi_plan=false pero la oferta tiene {len(config.offer.plans)} planes.")
    entries = config.offer.plans or (config.offer.catalog.items if config.offer.catalog else [])
    if features is not None and features.multi_currency is False and any(len(entry.prices) > 1 for entry in entries):
        add("multi_moneda_contradice_oferta", "incoherencia", "features.multi_currency",
            "multi_currency=false pero la oferta tiene precios en más de una moneda.")

    modes = set(config.identity.service_modes or [])
    fulfillment = config.fulfillment
    if fulfillment is not None and config.identity.service_modes is not None:
        for mode, part in SERVICE_MODE_FULFILLMENT.items():
            option = getattr(fulfillment, part)
            available = bool(option and option.available)
            if mode in modes and not available:
                add("modalidad_sin_entrega", "incoherencia", f"fulfillment.{part}",
                    f"La modalidad '{mode}' está en service_modes, pero fulfillment.{part} no está disponible.")
            if available and mode not in modes:
                add("entrega_sin_modalidad", "incoherencia", "identity.service_modes",
                    f"fulfillment.{part} está disponible, pero service_modes no incluye '{mode}'.")

    closing = config.sales.closing
    collected = set(capabilities.data_collection.fields) if capabilities.data_collection.enabled else set()
    for item in (closing.required_data if closing else None) or []:
        field = REQUIRED_DATA_FIELDS.get(item)
        if field and field not in collected:
            add("dato_de_cierre_no_solicitado", "incoherencia", "sales.closing.required_data",
                f"El cierre necesita '{item}', pero data_collection no pide '{field}'.")

    available = config.offer_names(available_only=True)
    for rule in config.sales.recommendation_rules or []:
        if rule.recommend not in available:
            add("recomienda_oferta_no_disponible", "incoherencia", "sales.recommendation_rules",
                f"Se recomienda '{rule.recommend}', que no está disponible.")

    for promotion in config.terms.promotions or []:
        if promotion.valid_until is not None and promotion.valid_until < today:
            add("promocion_vencida", "incoherencia", "terms.promotions",
                f"La promoción '{promotion.name}' venció el {promotion.valid_until.isoformat()}.")

    if not capabilities.service_channels:
        add("sin_canales_de_atencion", "incompleto", "capabilities.service_channels",
            "No hay canales de atención: el asistente no sabe por dónde atiende el negocio.")

    if fulfillment is not None and fulfillment.scheduling is not None and fulfillment.scheduling.required and not config.identity.opening_hours:
        add("agenda_sin_horarios", "incompleto", "identity.opening_hours",
            "El servicio requiere agendar, pero no hay horarios de atención.")

    found.extend(_live_advisories(config))
    return found


# Avisos que el panel calcula en vivo mientras se edita (`apps/admin-web/src/domain/validation/rules.ts`), con el mismo campo y el
# mismo texto: así el agente que trabaja por MCP ve lo mismo que la persona en la pantalla. Los casos compartidos están en
# `project/config/contracts/v1/advisory-cases.json` y los prueban los dos lados.
LIVE_ADVISORY_CODES = ("sin_direccion", "sin_medios_de_pago", "sin_problemas_del_cliente", "sin_mensaje_de_pago_reportado")


def _live_advisories(config: BusinessConfig) -> list[Diagnostic]:
    found: list[Diagnostic] = []
    location = config.identity.location
    if location is not None and location.type in ("fisico", "mixto") and not (location.address or "").strip():
        found.append(Diagnostic("sin_direccion", "incompleto", "identity.location.address", "Sin dirección, el asistente no podrá decir dónde queda tu local."))

    has_link = any(profile.link and profile.link_enabled is not False for profile in config.payments)
    has_transfer = False
    # Varias cuentas del mismo tipo están bien: el cliente recibe la del banco que nombra, o todas las de ese tipo juntas.
    for profile in config.payments:
        active = [method.type for method in profile.transfer_methods if profile.transfer_enabled and method.enabled is not False]
        has_transfer = has_transfer or bool(active)
    if not has_link and not has_transfer:
        found.append(Diagnostic("sin_medios_de_pago", "incompleto", "payments", "No hay ningún medio de pago: el asistente no podrá indicar cómo pagar."))

    sales = config.sales
    if not sales.customer_problems and not (sales.buying_motivation and sales.buying_motivation.primary):
        found.append(Diagnostic("sin_problemas_del_cliente", "incompleto", "sales.customer_problems",
                                "Cuéntale al asistente qué problemas resuelves o por qué te compran; le ayuda a vender mejor."))

    if not (config.messages.payment_reported or "").strip():
        found.append(Diagnostic("sin_mensaje_de_pago_reportado", "incompleto", "messages.payment_reported",
                                "Sin este mensaje, el asistente responderá con sus propias palabras cuando el cliente diga que ya pagó."))
    return found
