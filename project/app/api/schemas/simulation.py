from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    user_message: str = Field(min_length=1, max_length=2000)
    user_id: str | None = None
    yaml_config: dict = Field(default_factory=dict)
    faq_results: list[dict] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    reply: str
    ai_used: bool
    metadata: dict = Field(default_factory=dict)
