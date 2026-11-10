"""Los modelos de OpenRouter que puede elegir un negocio para su asistente.

Solo se ofrecen los que responden en el formato que usa el motor (JSON, `response_format`): con los demás, cada respuesta podría
llegar sin la intención ni los datos de pago. Los precios son los de OpenRouter, en dólares por millón de tokens.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.business_config.ai_settings import is_model_id

# Buenos en español, rápidos y baratos para conversar por chat. Solo se muestran los que OpenRouter tenga disponibles.
RECOMMENDED_MODELS = (
    "openai/gpt-4o-mini",
    "google/gemini-2.5-flash",
    "openai/gpt-4.1-mini",
    "anthropic/claude-haiku-4.5",
    "deepseek/deepseek-chat-v3.1",
    "mistralai/mistral-small-3.2-24b-instruct",
)


@dataclass(frozen=True)
class AIModel:
    id: str
    name: str
    provider: str
    prompt_usd_per_million: float
    completion_usd_per_million: float
    context_length: int

    def __post_init__(self) -> None:
        if not is_model_id(self.id):
            raise ValueError("identificador de modelo no válido")

    @property
    def free(self) -> bool:
        return self.prompt_usd_per_million == 0 and self.completion_usd_per_million == 0

    @property
    def recommended(self) -> bool:
        return self.id in RECOMMENDED_MODELS


@dataclass(frozen=True)
class ModelCatalog:
    """Lo que el panel muestra para elegir: los recomendados primero y el modelo que usa el sistema si no se elige ninguno."""

    default_model: str
    models: list[AIModel]

    def ids(self) -> set[str]:
        return {model.id for model in self.models}


def sorted_for_choice(models: list[AIModel]) -> list[AIModel]:
    """Recomendados en su orden; después, el resto por proveedor y nombre."""
    order = {model_id: position for position, model_id in enumerate(RECOMMENDED_MODELS)}
    return sorted(models, key=lambda model: (order.get(model.id, len(order)), model.provider.lower(), model.name.lower()))
