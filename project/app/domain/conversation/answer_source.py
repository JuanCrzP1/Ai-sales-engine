"""De dónde salió una respuesta del motor que no escribió la IA: el saludo del negocio o el mensaje de respaldo.

El motor marca cada respuesta con su origen (`metadata["source"]`). Cuando no la escribió la IA hay dos casos muy distintos:

- el **saludo del negocio** (Mensajes → Bienvenida): lo normal al empezar una conversación; no es una falla;
- el **mensaje de respaldo**: la IA no pudo responder (sin clave, sin saldo, el proveedor caído, una respuesta que no sirvió).

Hasta el 24 nov 2026 quien mostraba el resultado solo miraba «¿respondió la IA?»: «Probar asistente» ponía «Respondió sin la IA:
revisa la clave o el modelo» debajo del saludo del negocio, y la API del asistente devolvía `fallback: true` con él.
"""
from __future__ import annotations

# El origen con el que el motor marca el saludo del negocio (`application/pipeline/conversation_flow.py`).
WELCOME_SOURCE = "initial_message"


def is_welcome(metadata: dict | None) -> bool:
    """Si la respuesta es el saludo que el negocio escribió en el panel."""
    return isinstance(metadata, dict) and str(metadata.get("source") or "") == WELCOME_SOURCE


def is_fallback(ai_used: bool, metadata: dict | None) -> bool:
    """Si la IA no pudo responder y salió el mensaje de respaldo. El saludo del negocio no es una falla."""
    return not ai_used and not is_welcome(metadata)
