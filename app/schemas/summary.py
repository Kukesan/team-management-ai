from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class SummaryRequest(BaseModel):
    week_start: date
    project_id: UUID | None = None


class SummaryResponse(BaseModel):
    summary_markdown: str
    week_start: date
    project_id: UUID | None
    generated_at: datetime
