"""Diagnóstico de un BusinessConfig válido: incoherencias y datos incompletos que no bloquean.

La validación del contrato (`contract.py`) rechaza los documentos rotos: referencias inexistentes,
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
    if capabilities.closing_methods.payment_link and not any(profile.link for profile in config.payments):
        add("cierre_por_link_sin_link", "incoherencia", "capabilities.closing_methods.payment_link",
            "El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link.")

    referenced = {plan.payment_profile for plan in config.offer.plans or []}
    if config.offer.catalog is not None:
        referenced.add(config.offer.catalog.payment_profile)
    for profile in config.payments:
        if profile.id not in referenced:
            add("perfil_de_pago_sin_uso", "incoherencia", f"payments[id={profile.id}]",
                f"El perfil de pago '{profile.id}' no lo usa ningún plan ni el catálogo.")

    if config.engine is not None and config.engine.features.catalog_mode != (config.offer.model == "catalog"):
        add("modo_catalogo_contradice_oferta", "incoherencia", "engine.features.catalog_mode",
            f"catalog_mode={config.engine.features.catalog_mode} pero la oferta es de tipo '{config.offer.model}'.")

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

    if capabilities.data_collection.enabled and not capabilities.data_collection.consent_notice:
        add("datos_sin_aviso_de_tratamiento", "incompleto", "capabilities.data_collection.consent_notice",
            "Se piden datos personales sin un aviso de tratamiento de datos.")

    if fulfillment is not None and fulfillment.scheduling is not None and fulfillment.scheduling.required and not config.identity.opening_hours:
        add("agenda_sin_horarios", "incompleto", "identity.opening_hours",
            "El servicio requiere agendar, pero no hay horarios de atención.")

    return found
