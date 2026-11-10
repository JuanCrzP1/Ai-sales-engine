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
