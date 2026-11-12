"""Límites de uso: cuántas veces seguidas se puede hacer algo que gasta la clave de IA de un negocio.

Cada límite cuenta por ventanas fijas de tiempo (por ejemplo, 20 mensajes por minuto). Protegen al negocio de que alguien
con acceso al panel, o un script con su sesión, le gaste el saldo de OpenRouter en minutos.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageLimit:
    name: str
    limit: int
    window_seconds: int

    def __post_init__(self) -> None:
        if self.limit < 1 or self.window_seconds < 1:
            raise ValueError("un límite de uso necesita un máximo y una ventana positivos")


# Probar el asistente: una persona conversa a ritmo humano; un negocio entero, con su equipo, tiene un techo por hora.
PLAYGROUND_PER_USER = UsageLimit("playground_user", limit=20, window_seconds=60)
PLAYGROUND_PER_BUSINESS = UsageLimit("playground_business", limit=300, window_seconds=3600)
# Comprobar la clave llama a OpenRouter: basta con unas pocas veces seguidas.
AI_KEY_CHECKS_PER_USER = UsageLimit("ai_key_check_user", limit=10, window_seconds=600)
# Conectar WhatsApp llama al servidor de uazapi del negocio: guardar y pedir el QR, y consultar el estado mientras se escanea
# (el panel pregunta cada pocos segundos).
CHANNEL_SETUP_PER_USER = UsageLimit("channel_setup_user", limit=20, window_seconds=600)
CHANNEL_STATUS_PER_BUSINESS = UsageLimit("channel_status_business", limit=400, window_seconds=600)
# Respuestas del equipo desde la bandeja: cada una sale por WhatsApp, y los envíos masivos hacen que WhatsApp bloquee el número.
CONVERSATION_REPLIES_PER_USER = UsageLimit("conversation_reply_user", limit=120, window_seconds=600)
# La API del asistente: la llama un sistema (Leona, una web), no una persona. Cada clave tiene un ritmo; el negocio, un techo por
# hora entre todas sus claves, para que una clave filtrada o un ciclo mal armado no le gaste el saldo de IA.
ASSISTANT_API_PER_KEY = UsageLimit("assistant_api_key", limit=60, window_seconds=60)
ASSISTANT_API_PER_BUSINESS = UsageLimit("assistant_api_business", limit=1500, window_seconds=3600)
# Crear claves de API: pocas seguidas.
API_KEYS_PER_USER = UsageLimit("api_keys_user", limit=20, window_seconds=600)
# El servidor MCP: un agente que trabaja hace muchas llamadas seguidas (leer, editar, revisar), pero no infinitas. Protege la
# plataforma si una clave se filtra o un agente entra en un ciclo. Probar el asistente cuenta además como «Probar asistente».
MCP_PER_KEY = UsageLimit("mcp_key", limit=300, window_seconds=60)
