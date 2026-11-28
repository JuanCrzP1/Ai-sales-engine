"""La ficha de un cliente en el panel: verla, ponerle valor y responsable, y anotar. Cada usuario solo llega a sus negocios.

Quien atiende (también un asesor) puede cambiarla: es su herramienta de trabajo con el cliente.
"""
from __future__ import annotations

from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import CustomerCardStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.customer_card import CustomerCard, CustomerNote, DealChange, checked_note


class CustomerCardService:
    def __init__(self, storage: CustomerCardStorage, access: BusinessAccess) -> None:
        self._storage = storage
        self._access = access

    def card(self, principal: Principal, business: str, conversation_id: str) -> CustomerCard:
        self._access.require(principal, business)
        return self._storage.customer_card(business, conversation_id)

    def update(self, principal: Principal, business: str, conversation_id: str, changes: dict[str, Any]) -> CustomerCard:
        """`changes` trae solo lo que cambia: `amount` y `currency`, y/o `owner_id`. `CustomerCardError` si un dato no sirve."""
        self._access.require(principal, business)
        return self._storage.update_customer_deal(business, conversation_id, DealChange.checked(changes), by=principal.label)

    def add_note(self, principal: Principal, business: str, conversation_id: str, body: object) -> CustomerNote:
        self._access.require(principal, business)
        return self._storage.add_customer_note(business, conversation_id, checked_note(body), author=principal.label)

    def delete_note(self, principal: Principal, business: str, conversation_id: str, note_id: str) -> None:
        self._access.require(principal, business)
        self._storage.delete_customer_note(business, conversation_id, note_id)
