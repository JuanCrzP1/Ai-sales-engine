"""La lista de modelos de OpenRouter (implementa `AIModelCatalog`).

`GET /api/v1/models` es público: no usa la clave de ningún negocio ni gasta créditos. La lista se guarda una hora en memoria. Si
OpenRouter no responde, se usa la última que se tenga; si nunca se cargó, falla y el panel deja escribir el modelo a mano.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable

import httpx

from app.domain.business_config.ai_models import AIModel
from app.domain.business_config.ai_settings import is_model_id
from app.domain.business_config.errors import ModelCatalogUnavailableError
from app.utils.logger import logger

MODELS_URL = "https://openrouter.ai/api/v1/models"
TIMEOUT_SECONDS = 10.0
CACHE_SECONDS = 3600
PER_MILLION = 1_000_000


def _price(pricing: dict, key: str) -> float | None:
    try:
        value = float(pricing.get(key))
    except (TypeError, ValueError):
        return None
    return value * PER_MILLION if value >= 0 else None


def _model(item: object) -> AIModel | None:
    """Un modelo que conversa en texto, con precio conocido y que responde en JSON; si no, None."""
    if not isinstance(item, dict):
        return None
    model_id = str(item.get("id") or "")
    architecture = item.get("architecture") if isinstance(item.get("architecture"), dict) else {}
    pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
    parameters = item.get("supported_parameters") if isinstance(item.get("supported_parameters"), list) else []
    prompt, completion = _price(pricing, "prompt"), _price(pricing, "completion")
    if (
        not is_model_id(model_id)
        or "text" not in (architecture.get("input_modalities") or [])
        or "text" not in (architecture.get("output_modalities") or [])
        or "response_format" not in parameters
        or prompt is None
        or completion is None
    ):
        return None
    provider, _, name = str(item.get("name") or model_id).partition(": ")
    if not name:
        provider, name = model_id.split("/", 1)[0], provider
    try:
        context = int(item.get("context_length") or 0)
    except (TypeError, ValueError):
        context = 0
    return AIModel(model_id, name.strip(), provider.strip(), round(prompt, 4), round(completion, 4), context)


def parse_models(payload: object) -> list[AIModel]:
    data = payload.get("data") if isinstance(payload, dict) else None
    models = [model for model in map(_model, data if isinstance(data, list) else []) if model is not None]
    if not models:
        raise ValueError("la lista de OpenRouter llegó vacía o con otro formato")
    return models


class OpenRouterModelCatalog:
    def __init__(self, *, client: httpx.Client | None = None, clock: Callable[[], float] = time.monotonic) -> None:
        self._client = client
        self._clock = clock
        self._models: list[AIModel] = []
        self._loaded_at: float | None = None
        self._lock = threading.Lock()

    def models(self) -> list[AIModel]:
        with self._lock:
            if self._loaded_at is not None and self._clock() - self._loaded_at < CACHE_SECONDS:
                return list(self._models)
            try:
                response = (self._client or httpx).get(MODELS_URL, timeout=TIMEOUT_SECONDS)
                response.raise_for_status()
                self._models = parse_models(response.json())
                self._loaded_at = self._clock()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("openrouter_models_unavailable", extra={"error": type(exc).__name__, "cached": len(self._models)})
                if not self._models:
                    raise ModelCatalogUnavailableError("no se pudo cargar la lista de modelos de OpenRouter") from exc
            return list(self._models)
