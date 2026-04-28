from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MessageDirectionSchema(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class ConversationMessageCreate(BaseModel):
    client_id: int
    message_text: str = Field(min_length=1, max_length=2000)
    direction: MessageDirectionSchema
    intent: str | None = None


class ConversationMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    client_id: int
    channel: str
    message_text: str
    direction: MessageDirectionSchema
    intent: str | None = None
    ai_used: bool
    created_at: datetime


class IncomingWhatsAppMessage(BaseModel):
    phone_number: str
    message_text: str = Field(min_length=1, max_length=2000)
    profile_name: str | None = None


class ReplyMediaOut(BaseModel):
    key: str | None = None
    type: str = 'image'
    url: str
    caption: str | None = None
    alt_text: str | None = None


class ReplyMenuItemOut(BaseModel):
    id: str
    title: str
    description: str | None = None


class ReplyMenuOut(BaseModel):
    key: str | None = None
    type: str = 'buttons'
    title: str | None = None
    body: str | None = None
    footer: str | None = None
    button_text: str | None = None
    fallback_text: str | None = None
    items: list[ReplyMenuItemOut] = Field(default_factory=list)


class ReplyPayloadOut(BaseModel):
    text: str = ''
    media: list[ReplyMediaOut] = Field(default_factory=list)
    menu: ReplyMenuOut | None = None
    fallback_text: str = ''
    source_key: str | None = None
    metadata: dict = Field(default_factory=dict)


class ConversationReply(BaseModel):
    client_id: int
    lead_status: str
    intent: str
    faq_matches: list[str]
    reply: str
    ai_used: bool
    action: str | None = None
    action_data: dict = Field(default_factory=dict)
    handoff_requested: bool = False
    handoff_reason: str | None = None
    business_hours_status: str = "inside_hours"
    channel: str = "whatsapp"
    score: dict[str, float] = Field(default_factory=dict)
    message_score: dict = Field(default_factory=dict)
    close_probability: float = 0.0
    issues: list[str] = Field(default_factory=list)
    optimized: bool = False
    optimization_fallback: bool = False
    optimization_attempts: int = 0
    optimization_issues: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    blocked_by_guard: bool = False
    final_source: str = ''
    guard_reason: str | None = None
    greeting_source: str | None = None
    ai_calls_per_turn: int = 0
    response_modified_layers: int = 0
    score_thresholds: dict = Field(default_factory=dict)
    reply_payload: ReplyPayloadOut | None = None
    inbound_message_id: int
    outbound_message_id: int
