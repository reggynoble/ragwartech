from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=5000)


class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)


class ChatLatency(BaseModel):
    retrieval_ms: float | None = None
    context_ms: float | None = None
    prompt_ms: float | None = None
    llm_ms: float | None = None
    total_ms: float


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = Field(default_factory=list)
    latency: ChatLatency | None = None
