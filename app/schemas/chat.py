from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    # Bounded so a caller can't attach an unbounded conversation and balloon token
    # cost/latency -- team-management-api's ChatRequestDtoValidator enforces the same limit
    # closer to the user; this is defense in depth for direct callers of this service.
    history: list[ChatMessage] = Field(default_factory=list, max_length=40)


class ChatResponse(BaseModel):
    answer: str
    tools_used: list[str]
