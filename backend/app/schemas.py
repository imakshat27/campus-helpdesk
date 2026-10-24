from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None

class Source(BaseModel):
    id: str
    document_id: str
    title: str
    heading: str
    content: str
    source_url: str | None = None
    campus: str | None = None
    retrieved_at: str | None = None

class TicketOffer(BaseModel):
    message_id: str
    query: str

class EscalationRequest(BaseModel):
    message_id: UUID
    confirmed: Literal[True]

    @field_validator('confirmed', mode='before')
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError('Explicit confirmation must be the boolean true.')
        return value

class ChatResponse(BaseModel):
    conversation_id: str
    outcome: Literal['answered', 'clarification', 'needs_staff_confirmation', 'conversation', 'escalated']
    message: str
    sources: list[Source] = []
    ticket_reference: str | None = None
    user_message_id: str
    ticket_offer: TicketOffer | None = None

class Generation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    outcome: Literal['answered', 'clarification', 'unsupported']
    message: str = Field(min_length=1, max_length=6000)
    source_ids: list[str]

class TicketUpdate(BaseModel):
    status: Literal['open', 'resolved']
