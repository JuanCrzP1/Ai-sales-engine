from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LeadStatusSchema(str, Enum):
    frio = "frio"
    interesado = "interesado"
    caliente = "caliente"


class ClientBase(BaseModel):
    name: str | None = Field(default=None, examples=["Carlos Pérez"])
    phone_number: str = Field(examples=["+50688887777"])


class ClientCreate(ClientBase):
    pass


class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[128])
    client_code: str = Field(description="Código visible consecutivo por tenant.", examples=["001"])
    tenant_id: int = Field(examples=[1])
    lead_status: LeadStatusSchema = Field(examples=[LeadStatusSchema.interesado])
    last_intent: str | None = None
    last_contact_at: datetime
    created_at: datetime
