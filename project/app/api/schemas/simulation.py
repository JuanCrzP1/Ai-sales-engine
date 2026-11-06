from pydantic import BaseModel, ConfigDict, Field


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_message: str = Field(min_length=1, max_length=2000)
    # Etiqueta de la conversación simulada de quien llama; no identifica a ningún cliente real.
    user_id: str | None = Field(default=None, max_length=64)
    faq_results: list[dict] = Field(default_factory=list)


class SimulationMetadata(BaseModel):
    """Lista cerrada de metadatos de la simulación: etiquetas, nunca configuración ni memoria."""

    source: str | None = None
    intent: str | None = None
    conversation_state: str | None = None
    tenant_slug: str | None = None


class SimulationResponse(BaseModel):
    reply: str
    ai_used: bool
    metadata: SimulationMetadata
