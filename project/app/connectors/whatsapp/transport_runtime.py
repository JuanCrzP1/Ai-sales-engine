from __future__ import annotations

from app.connectors.whatsapp.transport import TransportSenderMixin


class WhatsAppService(TransportSenderMixin):
    """Transporte WhatsApp: fachada de envío outbound."""
