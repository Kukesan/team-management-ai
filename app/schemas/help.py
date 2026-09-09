from typing import Literal

from pydantic import BaseModel, Field


class HelpMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class HelpRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    # See ChatRequest.history -- same bound, same reasoning.
    history: list[HelpMessage] = Field(default_factory=list, max_length=40)


class HelpResponse(BaseModel):
    answer: str
