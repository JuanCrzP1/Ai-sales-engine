from __future__ import annotations

from app.connectors.whatsapp.transport import TransportSenderMixin
from app.infrastructure.config.config_service import ConfigService


class WhatsAppService(TransportSenderMixin):
    """Transporte WhatsApp: fachada de envío outbound."""

    def __init__(self, config_service: ConfigService | None = None):
        self.config = config_service or ConfigService()
