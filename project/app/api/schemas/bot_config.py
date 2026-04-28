from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BotConfigUpdate(BaseModel):
    company_name: str
    system_prompt: str
    greeting_message: str
    fallback_message: str
    sensitive_fallback: str
    model_name: str
    temperature: float
    enable_ai_engine: bool = True
    enable_optimizer: bool = True


class BotConfigOut(BotConfigUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    updated_at: datetime
