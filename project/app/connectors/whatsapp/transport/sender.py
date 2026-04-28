from __future__ import annotations

from app.connectors.tenant_guard import resolve_connector_tenant
from app.models import Tenant
from app.services.tenant_connector_service import resolve_outbound_provider_for_tenant


class TransportSenderMixin:
    def send_message(self, tenant: Tenant, phone_number: str, message: str | dict, provider: str | None = None) -> bool:
        from app.connectors.router import get_sender

        resolve_connector_tenant(getattr(tenant, "slug", None))

        resolved_provider = provider or resolve_outbound_provider_for_tenant(tenant=tenant, channel="whatsapp")
        sender = get_sender("whatsapp", provider=resolved_provider, tenant=tenant)
        if sender is None:
            raise Exception("❌ WHATSAPP MESSAGE NOT SENT — CONFIG INVALID")

        return sender.send(tenant=tenant, phone_number=phone_number, message=message)
