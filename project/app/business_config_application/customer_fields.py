"""Los campos del cliente en el panel. Cada usuario solo llega a sus negocios.

Todo el que atiende ve los campos y llena sus valores en la ficha de cada cliente. Crear, renombrar, cambiar las opciones y borrar
campos es de quien configura el negocio (el dueño o un administrador): afecta a todos sus clientes.
"""
from __future__ import annotations

from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import CustomerFieldStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.customer_fields import CustomerField, FieldChange, FieldValue, FieldValues, NewField
from app.domain.business_config.team import ATTEND, CONFIGURE


class CustomerFieldService:
    def __init__(self, storage: CustomerFieldStorage, access: BusinessAccess) -> None:
        self._storage = storage
        self._access = access

    def fields(self, principal: Principal, business: str) -> list[CustomerField]:
        self._access.require(principal, business, ATTEND)
        return self._storage.customer_fields(business)

    def create(self, principal: Principal, business: str, *, name: object, kind: object, options: object = None) -> CustomerField:
        self._access.require(principal, business, CONFIGURE)
        return self._storage.create_customer_field(business, NewField.checked(name=name, kind=kind, options=options), created_by=principal.label)

    def update(self, principal: Principal, business: str, field_id: str, changes: dict[str, Any]) -> CustomerField:
        """`changes` trae solo lo que cambia: el nombre y/o las opciones de una lista."""
        self._access.require(principal, business, CONFIGURE)
        return self._storage.update_customer_field(business, field_id, FieldChange.checked(changes))

    def delete(self, principal: Principal, business: str, field_id: str) -> None:
        self._access.require(principal, business, CONFIGURE)
        self._storage.delete_customer_field(business, field_id)

    def set_values(self, principal: Principal, business: str, conversation_id: str, values: object) -> list[FieldValue]:
        """Cambia los valores que llegan (por id de campo; vacío o None lo deja vacío), a nombre de quien lo hace."""
        self._access.require(principal, business, ATTEND)
        return self._storage.set_customer_field_values(business, conversation_id, FieldValues.checked(values), by=principal.label)
