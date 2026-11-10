"""Comprueba con OpenRouter que la clave de un negocio es válida, sin gastar créditos (implementa `AIKeyVerifier`).

Usa `GET /api/v1/key`, que solo describe la clave con la que se llama. La clave nunca se registra ni se muestra.
"""
from __future__ import annotations

import httpx

from app.domain.business_config.ai_settings import AICredentials, KeyCheck

KEY_INFO_URL = "https://openrouter.ai/api/v1/key"
TIMEOUT_SECONDS = 10.0


class OpenRouterKeyVerifier:
    def __init__(self, *, client: httpx.Client | None = None) -> None:
        self._client = client

    def verify(self, credentials: AICredentials) -> KeyCheck:
        headers = {"Authorization": f"Bearer {credentials.api_key}"}
        try:
            if self._client is not None:
                response = self._client.get(KEY_INFO_URL, headers=headers, timeout=TIMEOUT_SECONDS)
            else:
                response = httpx.get(KEY_INFO_URL, headers=headers, timeout=TIMEOUT_SECONDS)
        except httpx.HTTPError:
            return KeyCheck(False, "No se pudo contactar a OpenRouter. Revisa la conexión a internet e inténtalo de nuevo.")
        if response.status_code in (401, 403):
            return KeyCheck(False, "OpenRouter rechazó la clave. Revísala o crea una nueva en openrouter.ai.")
        if response.status_code != 200:
            return KeyCheck(False, f"OpenRouter respondió con un error ({response.status_code}). Inténtalo de nuevo en unos minutos.")
        data = response.json().get("data") if isinstance(response.json(), dict) else {}
        data = data if isinstance(data, dict) else {}
        label = str(data.get("label") or "").strip()
        remaining = data.get("limit_remaining")
        details = []
        if label:
            details.append(f"clave «{label}»")
        if isinstance(remaining, (int, float)):
            details.append(f"saldo disponible: {remaining:.2f} USD")
        return KeyCheck(True, "La clave funciona" + (f" ({', '.join(details)})." if details else "."))
