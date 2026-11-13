"""Lo que el asistente recuerda de cada cliente, visto desde el panel: al eliminar un chat, el motor lo olvida todo.

El motor guarda su memoria aparte de la bandeja (`clients`, `conversation_messages` y `conversation_memory`, por negocio y número
del cliente) y una copia en RAM. Este adaptador implementa `ContactMemory` para la API del panel, que no conoce el motor.
"""
from __future__ import annotations

from app.domain.business_config.errors import AssistantUnavailableError
from app.utils.logger import logger


class EngineContactMemory:
    def forget(self, business_slug: str, contact_ref: str) -> None:
        from app.services.ai_service import GLOBAL_MEMORY_REPOSITORY

        try:
            GLOBAL_MEMORY_REPOSITORY.forget_contact(tenant_slug=business_slug, user_id=contact_ref)
        except Exception as exc:  # noqa: BLE001 - se informa al panel; se registra el tipo, nunca el número del cliente
            logger.error("memoria_del_cliente_no_borrada", extra={"tenant": business_slug, "error": type(exc).__name__})
            raise AssistantUnavailableError(
                "No se pudo borrar lo que el asistente recuerda de este cliente, así que el chat no se eliminó. Intenta de nuevo"
            ) from exc

    def forget_playground(self, business_slug: str, session_id: str | None = None) -> None:
        """Lo que el motor recuerda de las conversaciones de «Probar»: de una sesión, o de todas las del negocio."""
        from app.application.assistant_lab.engine_runner import PLAYGROUND_CONTACT_PREFIX, playground_contact
        from app.services.ai_service import GLOBAL_MEMORY_REPOSITORY

        try:
            if session_id:
                GLOBAL_MEMORY_REPOSITORY.forget_contact(tenant_slug=business_slug, user_id=playground_contact(session_id))
            else:
                GLOBAL_MEMORY_REPOSITORY.forget_contacts_with_prefix(tenant_slug=business_slug, prefix=PLAYGROUND_CONTACT_PREFIX)
        except Exception as exc:  # noqa: BLE001 - se informa al panel
            logger.error("memoria_de_pruebas_no_borrada", extra={"tenant": business_slug, "error": type(exc).__name__})
            raise AssistantUnavailableError("No se pudo borrar lo que el asistente recuerda de las pruebas, así que no se borraron. Intenta de nuevo") from exc

    def forget_business(self, business_slug: str) -> None:
        """Al eliminar un negocio: lo que el motor tiene en memoria de sus clientes (en la base se borra con el negocio)."""
        from app.services.ai_service import GLOBAL_MEMORY_REPOSITORY

        GLOBAL_MEMORY_REPOSITORY.forget_business(tenant_slug=business_slug)
