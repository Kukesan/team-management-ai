from typing import Literal

from pydantic import BaseModel, Field


class HelpMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class HelpRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[HelpMessage] = Field(default_factory=list)


class HelpResponse(BaseModel):
    answer: str
