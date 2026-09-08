from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.dependencies import RequestContext, get_current_context
from app.repositories import reports_repository as repo
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.llm import summarize

router = APIRouter()


@router.post("/summary", response_model=SummaryResponse)
async def summary(request: SummaryRequest, ctx: RequestContext = Depends(get_current_context)) -> SummaryResponse:
    week_end = request.week_start + timedelta(days=6)

    reports = await repo.get_reports(
        date_from=request.week_start, date_to=week_end, project_id=request.project_id
    )
    submission_status = await repo.get_submission_status(
        week_start=request.week_start, project_id=request.project_id
    )
    workload = await repo.get_workload_summary(
        date_from=request.week_start, date_to=week_end, project_id=request.project_id
    )

    markdown = await summarize(
        week_start=request.week_start.isoformat(),
        reports=reports,
        submission_status=submission_status,
        workload=workload,
    )

    return SummaryResponse(
        summary_markdown=markdown,
        week_start=request.week_start,
        project_id=request.project_id,
        generated_at=datetime.now(timezone.utc),
    )
