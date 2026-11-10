"""Plantillas de negocio: un documento comercial de ejemplo por tipo de negocio (restaurante, tienda, agencia...), para no empezar de cero.

Una plantilla nunca trae lo que es propio de un negocio real: ni datos de pago, ni marca, dirección, ciudad o zonas, ni pruebas de
confianza (serían testimonios inventados), ni políticas. Trae productos, precios, textos y estrategia de ejemplo para editar. Al crear un
negocio con ella se le ponen el identificador y el nombre que eligió la persona, y queda en borrador: nada le llega a un cliente hasta
que el negocio lo revise y lo publique.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any

from app.domain.business_config.contract import BusinessConfig

TEMPLATE_ID = re.compile(r"^[a-z0-9][a-z0-9_]*$")
# Lo que identifica a un negocio real: ninguna plantilla puede traerlo.
_PRIVATE_IDENTITY = ("brand_name", "credibility")
_PRIVATE_LOCATION = ("address", "city")
_SAMPLE_SLUG, _SAMPLE_NAME = "plantilla_de_prueba", "Negocio de prueba"


class TemplateNotFoundError(LookupError):
    """La plantilla pedida no existe."""


@dataclass(frozen=True)
class BusinessTemplate:
    id: str
    title: str
    description: str
    icon: str
    order: int
    document: dict[str, Any] = field(repr=False)

    def instantiate(self, tenant_slug: str, name: str) -> dict[str, Any]:
        """El documento del negocio nuevo: el de la plantilla con su identificador y su nombre."""
        document = copy.deepcopy(self.document)
        document["tenant_slug"] = tenant_slug
        document["identity"] = {**document["identity"], "name": name.strip()}
        return document


def _private_data(document: dict[str, Any]) -> list[str]:
    identity = document.get("identity") or {}
    location = identity.get("location") or {}
    found = [f"identity.{key}" for key in _PRIVATE_IDENTITY if identity.get(key)]
    found += [f"identity.location.{key}" for key in _PRIVATE_LOCATION if location.get(key)]
    if (location.get("coverage") or {}).get("zones"):
        found.append("identity.location.coverage.zones")
    if document.get("payments"):
        found.append("payments")
    if (document.get("terms") or {}).get("policies"):
        found.append("terms.policies")
    if "tenant_slug" in document:
        found.append("tenant_slug")
    return found


def template_from_dict(data: dict[str, Any]) -> BusinessTemplate:
    """Una plantilla leída de su archivo. Falla si le falta algo, si trae datos propios de un negocio o si no cumple el contrato."""
    template = BusinessTemplate(
        id=str(data["id"]),
        title=str(data["title"]).strip(),
        description=str(data["description"]).strip(),
        icon=str(data["icon"]).strip(),
        order=int(data["order"]),
        document=dict(data["document"]),
    )
    if not TEMPLATE_ID.match(template.id):
        raise ValueError(f"plantilla {template.id!r}: identificador no válido")
    if not (template.title and template.description and template.icon):
        raise ValueError(f"plantilla {template.id}: le falta título, descripción o ícono")
    private = _private_data(template.document)
    if private:
        raise ValueError(f"plantilla {template.id}: no puede traer datos propios de un negocio ({', '.join(private)})")
    BusinessConfig.model_validate(template.instantiate(_SAMPLE_SLUG, _SAMPLE_NAME))
    return template
