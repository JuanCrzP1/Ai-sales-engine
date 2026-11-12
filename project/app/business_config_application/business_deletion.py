"""Eliminar un negocio: todo lo suyo, para siempre, y solo si lo pide su dueño escribiendo su nombre.

En este orden, para no dejar nada a medias:
1. **Quién y qué:** solo el dueño (`BusinessAccess.require_owner`), y escribiendo el nombre del negocio (o su identificador).
2. **Lo que vive fuera de la base:** se cierra la sesión de WhatsApp y se borra su instancia en el servidor de WhatsApp. Si no se
   puede (el servidor no responde), no se borra NADA y se puede intentar de nuevo. Si la instancia ya no existía, se sigue.
3. **La base, en una transacción:** el negocio y todo lo que depende de él (versiones, datos de pago, conversaciones con sus fotos
   y audios, clientes, ventas, avisos, claves de API de ese negocio, ajustes, uso de la IA, miembros y, en la nube, la memoria del
   motor) se borran en cascada. Si algo falla, no se borra nada.
4. **La memoria en RAM** del motor sobre sus clientes: se olvida en esta instancia (las demás la leen de la base, que ya no la
   tiene). Si falla, el negocio ya está borrado: se registra y no se le cobra a la persona.

Las claves de la cuenta que entraban a «algunos» negocios pierden este; las de «todos» siguen con los demás.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.business_config_application.access import BusinessAccess
from app.business_config_application.channels import WhatsAppChannelService
from app.business_config_application.ports import ContactMemory
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.access import Principal
from app.domain.business_config.channels import ChannelError
from app.domain.business_config.errors import BusinessDeletionBlockedError, FieldIssue, InvalidFieldsError

logger = logging.getLogger("business_deletion")


def _comparable(text: object) -> str:
    return " ".join(str(text or "").split()).casefold()


@dataclass(frozen=True)
class DeletedBusiness:
    slug: str
    name: str
    whatsapp_disconnected: bool


class BusinessDeletionService:
    def __init__(
        self,
        configs: BusinessConfigService,
        access: BusinessAccess,
        *,
        whatsapp: WhatsAppChannelService | None = None,
        memory: ContactMemory | None = None,
    ) -> None:
        self._configs = configs
        self._access = access
        self._whatsapp = whatsapp
        self._memory = memory

    def delete(self, principal: Principal, business: str, confirmation: object) -> DeletedBusiness:
        self._access.require_owner(principal, business)
        summary = self._configs.get_business(business)
        typed = _comparable(confirmation)
        if not typed or typed not in (_comparable(summary.name), _comparable(summary.slug)):
            message = f"Escribe el nombre del negocio, «{summary.name}», para confirmar."
            raise InvalidFieldsError(message, [FieldIssue("confirm", message)])

        disconnected = self._close_whatsapp(business)
        self._configs.delete_business(business)
        self._forget_memory(business)
        logger.info("negocio_eliminado", extra={"tenant": business, "whatsapp": disconnected})
        return DeletedBusiness(slug=business, name=summary.name, whatsapp_disconnected=disconnected)

    def _close_whatsapp(self, business: str) -> bool:
        """True si el negocio tenía WhatsApp y se cerró. Sin conexión guardada no hay nada que cerrar."""
        if self._whatsapp is None or self._whatsapp.get(business).connection is None:
            return False
        try:
            self._whatsapp.disconnect(business)
        except ChannelError as exc:
            if not exc.gone:
                logger.warning("negocio_no_eliminado_whatsapp", extra={"tenant": business, "error": type(exc).__name__})
                raise BusinessDeletionBlockedError(
                    "No se pudo desconectar WhatsApp, así que no se eliminó nada. Intenta de nuevo en unos minutos."
                ) from exc
        return True

    def _forget_memory(self, business: str) -> None:
        if self._memory is None:
            return
        try:
            self._memory.forget_business(business)
        except Exception:  # noqa: BLE001 - el negocio ya se borró; la copia en RAM de esta instancia se pierde al reiniciar
            logger.exception("memoria_del_negocio_no_olvidada", extra={"tenant": business})
