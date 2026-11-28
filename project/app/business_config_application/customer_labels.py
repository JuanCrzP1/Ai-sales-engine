"""Las etiquetas de los clientes en el panel. Cada usuario solo llega a sus negocios.

Quien atiende las ve, se las pone a sus clientes, crea etiquetas y les cambia el color. Cambiarles el nombre y borrarlas es de quien
configura el negocio (el dueño o un administrador): afecta a todos los clientes que la llevan.
"""
from __future__ import annotations

from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import CustomerLabelStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.commerce import Customer
from app.domain.business_config.customer_labels import Label, LabelChange, checked_color, checked_name, checked_selection
from app.domain.business_config.team import ATTEND, CONFIGURE


class CustomerLabelService:
    def __init__(self, storage: CustomerLabelStorage, access: BusinessAccess) -> None:
        self._storage = storage
        self._access = access

    def labels(self, principal: Principal, business: str) -> list[Label]:
        self._access.require(principal, business)
        return self._storage.labels(business)

    def create(self, principal: Principal, business: str, *, name: object, color: object = None) -> Label:
        self._access.require(principal, business)
        return self._storage.create_label(business, checked_name(name), checked_color(color), created_by=principal.label)

    def update(self, principal: Principal, business: str, label_id: str, changes: dict[str, Any]) -> Label:
        """`changes` trae solo lo que cambia. El color lo cambia quien atiende; el nombre, quien configura el negocio."""
        change = LabelChange.checked(changes)
        self._access.require(principal, business, CONFIGURE if change.name is not None else ATTEND)
        return self._storage.update_label(business, label_id, change)

    def delete(self, principal: Principal, business: str, label_id: str) -> None:
        self._access.require(principal, business, CONFIGURE)
        self._storage.delete_label(business, label_id)

    def assign(self, principal: Principal, business: str, conversation_id: str, label_ids: object) -> Customer:
        """Deja al cliente con esas etiquetas (y solo esas)."""
        self._access.require(principal, business)
        return self._storage.set_customer_labels(business, conversation_id, checked_selection(label_ids))
