"""Tool definitions the LLM can call during the chat tool-use loop (see llm.py).
Each tool wraps one reports_repository query with light input parsing/validation --
the model never writes SQL, it only chooses a tool name + JSON arguments matching the
schema below, so there's no injection surface here beyond normal parameterized
query bugs.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.core.errors import ToolExecutionError
from app.repositories import reports_repository as repo

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "List all active projects with their id and name. Call this first "
            "when the user refers to a project by name (e.g. \"the design team\", \"Client A\") "
            "so you can resolve the name to a project_id before calling other tools.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_team_members",
            "description": "List active team members (id, full name, role), optionally scoped to "
            "one project. Call this to resolve a person's name to a user_id, or to see who is on "
            "a project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "UUID of a project to filter by. Omit for all members."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reports",
            "description": "Fetch weekly reports (with their full tasks completed, blockers, "
            "achievements, and hours breakdown) in a date range. Use this to answer questions "
            "about what someone worked on, what blockers/achievements were reported, task status "
            "or completion percentages, or time spent on specific tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Start of the week range, ISO date (YYYY-MM-DD)."},
                    "date_to": {"type": "string", "description": "End of the week range, ISO date (YYYY-MM-DD)."},
                    "project_id": {"type": "string", "description": "Optional UUID to filter to one project."},
                    "user_id": {"type": "string", "description": "Optional UUID to filter to one team member."},
                    "status": {
                        "type": "string",
                        "description": "Optional report status filter.",
                        "enum": ["Draft", "Submitted", "NeedsCorrection", "Approved"],
                    },
                },
                "required": ["date_from", "date_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_submission_status",
            "description": "For a single week, list every team member's report status per assigned "
            "project (Draft/Submitted/NeedsCorrection/Approved/NotStarted). Use this for compliance "
            "questions like who hasn't submitted yet, or who is in Needs Correction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "week_start": {"type": "string", "description": "ISO date (YYYY-MM-DD) of the week's start."},
                    "project_id": {"type": "string", "description": "Optional UUID to filter to one project."},
                },
                "required": ["week_start"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_workload_summary",
            "description": "Aggregate hours/report counts by project and by task type (Development, "
            "Testing, Meetings, etc.) over a date range. Use this for workload distribution, "
            "workload-imbalance, or \"how much time went to meetings vs development\" questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "ISO date (YYYY-MM-DD)."},
                    "date_to": {"type": "string", "description": "ISO date (YYYY-MM-DD)."},
                    "project_id": {"type": "string", "description": "Optional UUID to filter to one project."},
                },
                "required": ["date_from", "date_to"],
            },
        },
    },
]


def _parse_date(value: str, field: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise ToolExecutionError(f"Invalid date for '{field}': {value!r} (expected YYYY-MM-DD)") from exc


def _parse_uuid(value: Any, field: str) -> UUID | None:
    if value in (None, ""):
        return None
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ToolExecutionError(f"Invalid UUID for '{field}': {value!r}") from exc


async def execute_tool(name: str, tool_input: dict) -> Any:
    if name == "list_projects":
        return await repo.list_projects()

    if name == "list_team_members":
        return await repo.list_team_members(project_id=_parse_uuid(tool_input.get("project_id"), "project_id"))

    if name == "get_reports":
        if "date_from" not in tool_input or "date_to" not in tool_input:
            raise ToolExecutionError("get_reports requires 'date_from' and 'date_to'.")
        return await repo.get_reports(
            date_from=_parse_date(tool_input["date_from"], "date_from"),
            date_to=_parse_date(tool_input["date_to"], "date_to"),
            project_id=_parse_uuid(tool_input.get("project_id"), "project_id"),
            user_id=_parse_uuid(tool_input.get("user_id"), "user_id"),
            status=tool_input.get("status"),
        )

    if name == "get_submission_status":
        if "week_start" not in tool_input:
            raise ToolExecutionError("get_submission_status requires 'week_start'.")
        return await repo.get_submission_status(
            week_start=_parse_date(tool_input["week_start"], "week_start"),
            project_id=_parse_uuid(tool_input.get("project_id"), "project_id"),
        )

    if name == "get_workload_summary":
        if "date_from" not in tool_input or "date_to" not in tool_input:
            raise ToolExecutionError("get_workload_summary requires 'date_from' and 'date_to'.")
        return await repo.get_workload_summary(
            date_from=_parse_date(tool_input["date_from"], "date_from"),
            date_to=_parse_date(tool_input["date_to"], "date_to"),
            project_id=_parse_uuid(tool_input.get("project_id"), "project_id"),
        )

    raise ToolExecutionError(f"Unknown tool: {name}")
