"""Read-only queries against the Postgres database team-management-api (EF Core)
owns and migrates. Table/column names are exactly the C# entity property names --
EF Core here uses no snake_case convention and no ToTable() overrides -- so every
identifier is quoted PascalCase (e.g. "Reports", "ReportTaskItems", "WeekStartDate").

Every enum column (Report.Status, ReportTaskItem.Priority/Status,
ReportHoursBreakdown.TaskType) is stored via HasConversion<string>(), so filters and
returned values are the literal C# enum member text ("NeedsCorrection", "InProgress",
...), not integers.

This module issues SELECT statements only -- see the AI service README/plan for the
recommended dedicated read-only DB role. No INSERT/UPDATE/DELETE belongs here.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from app.db.pool import get_pool


def _clean(value: Any) -> Any:
    """asyncpg hands back uuid.UUID/date/Decimal objects that aren't JSON-serializable
    as-is; normalize recursively before returning rows to callers (tool results get
    JSON-encoded for the model, response models get JSON-encoded for the HTTP response)."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    return value


def _row_to_dict(record) -> dict:
    return {k: _clean(v) for k, v in dict(record).items()}


async def list_projects() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        'SELECT "Id" AS id, "Name" AS name FROM "Projects" WHERE "IsActive" = true ORDER BY "Name"'
    )
    return [_row_to_dict(r) for r in rows]


async def list_team_members(project_id: Optional[UUID] = None) -> list[dict]:
    pool = get_pool()
    if project_id is None:
        rows = await pool.fetch(
            """
            SELECT DISTINCT u."Id" AS id, u."FullName" AS full_name, ro."Name" AS role
            FROM "AspNetUsers" u
            JOIN "AspNetUserRoles" ur ON ur."UserId" = u."Id"
            JOIN "AspNetRoles" ro ON ro."Id" = ur."RoleId"
            WHERE u."IsActive" = true
            ORDER BY u."FullName"
            """
        )
    else:
        rows = await pool.fetch(
            """
            SELECT DISTINCT u."Id" AS id, u."FullName" AS full_name, ro."Name" AS role
            FROM "AspNetUsers" u
            JOIN "AspNetUserRoles" ur ON ur."UserId" = u."Id"
            JOIN "AspNetRoles" ro ON ro."Id" = ur."RoleId"
            JOIN "ProjectAssignments" pa ON pa."UserId" = u."Id"
            WHERE u."IsActive" = true AND pa."ProjectId" = $1
            ORDER BY u."FullName"
            """,
            project_id,
        )
    return [_row_to_dict(r) for r in rows]


async def get_reports(
    date_from: date,
    date_to: date,
    project_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT
            r."Id" AS id,
            r."WeekStartDate" AS week_start,
            r."WeekEndDate" AS week_end,
            r."Status" AS status,
            u."Id" AS user_id,
            u."FullName" AS user_name,
            p."Id" AS project_id,
            p."Name" AS project_name,
            r."Notes" AS notes,
            COALESCE(tasks.tasks, '[]'::json) AS tasks,
            COALESCE(next_week_tasks.next_week_tasks, '[]'::json) AS next_week_tasks,
            COALESCE(blockers.blockers, '[]'::json) AS blockers,
            COALESCE(achievements.achievements, '[]'::json) AS achievements,
            COALESCE(hours.hours, '[]'::json) AS hours
        FROM "Reports" r
        JOIN "AspNetUsers" u ON u."Id" = r."UserId"
        JOIN "Projects" p ON p."Id" = r."ProjectId"
        LEFT JOIN LATERAL (
            SELECT json_agg(json_build_object(
                'task_name', t."TaskName",
                'priority', t."Priority",
                'planned_percent', t."PlannedPercent",
                'actual_percent', t."ActualPercent",
                'status', t."Status",
                'time_planned_hours', t."TimePlannedHours",
                'time_spent_hours', t."TimeSpentHours",
                'output', t."Output"
            )) AS tasks
            FROM "ReportTaskItems" t WHERE t."ReportId" = r."Id"
        ) tasks ON true
        LEFT JOIN LATERAL (
            SELECT json_agg(json_build_object('description', n."Description")) AS next_week_tasks
            FROM "ReportNextWeekTasks" n WHERE n."ReportId" = r."Id"
        ) next_week_tasks ON true
        LEFT JOIN LATERAL (
            SELECT json_agg(json_build_object(
                'description', b."Description",
                'is_key_issue', b."IsKeyIssue",
                'is_resolved', b."IsResolved"
            )) AS blockers
            FROM "ReportBlockers" b WHERE b."ReportId" = r."Id"
        ) blockers ON true
        LEFT JOIN LATERAL (
            SELECT json_agg(json_build_object(
                'description', a."Description",
                'is_key_achievement', a."IsKeyAchievement"
            )) AS achievements
            FROM "ReportAchievements" a WHERE a."ReportId" = r."Id"
        ) achievements ON true
        LEFT JOIN LATERAL (
            SELECT json_agg(json_build_object(
                'task_type', h."TaskType",
                'hours', h."Hours"
            )) AS hours
            FROM "ReportHoursBreakdowns" h WHERE h."ReportId" = r."Id"
        ) hours ON true
        WHERE r."WeekStartDate" >= $1 AND r."WeekStartDate" <= $2
          AND ($3::uuid IS NULL OR r."ProjectId" = $3)
          AND ($4::uuid IS NULL OR r."UserId" = $4)
          AND ($5::text IS NULL OR r."Status" = $5)
          -- "Draft -- only visible to them" (spec Sec3): /chat and /summary are Manager/Admin
          -- tools, so a still-private draft must never reach the model, regardless of the
          -- `status` filter the model itself requested.
          AND r."Status" != 'Draft'
        ORDER BY r."WeekStartDate" DESC, u."FullName"
        LIMIT $6
        """,
        date_from,
        date_to,
        project_id,
        user_id,
        status,
        limit,
    )
    return [_row_to_dict(r) for r in rows]


async def get_submission_status(week_start: date, project_id: Optional[UUID] = None) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT
            u."Id" AS user_id,
            u."FullName" AS user_name,
            p."Id" AS project_id,
            p."Name" AS project_name,
            COALESCE(r."Status", 'NotStarted') AS status
        FROM "ProjectAssignments" pa
        JOIN "AspNetUsers" u ON u."Id" = pa."UserId"
        JOIN "Projects" p ON p."Id" = pa."ProjectId"
        LEFT JOIN "Reports" r
            ON r."UserId" = pa."UserId" AND r."ProjectId" = pa."ProjectId" AND r."WeekStartDate" = $1
        WHERE u."IsActive" = true AND ($2::uuid IS NULL OR p."Id" = $2)
        ORDER BY u."FullName"
        """,
        week_start,
        project_id,
    )
    return [_row_to_dict(r) for r in rows]


async def get_workload_summary(
    date_from: date, date_to: date, project_id: Optional[UUID] = None
) -> dict:
    pool = get_pool()
    by_project = await pool.fetch(
        """
        SELECT
            p."Id" AS project_id,
            p."Name" AS project_name,
            COUNT(DISTINCT r."Id") AS report_count,
            COALESCE(SUM(t."TimeSpentHours"), 0) AS total_hours_spent
        FROM "Reports" r
        JOIN "Projects" p ON p."Id" = r."ProjectId"
        LEFT JOIN "ReportTaskItems" t ON t."ReportId" = r."Id"
        WHERE r."WeekStartDate" >= $1 AND r."WeekStartDate" <= $2
          AND ($3::uuid IS NULL OR r."ProjectId" = $3)
        GROUP BY p."Id", p."Name"
        ORDER BY total_hours_spent DESC
        """,
        date_from,
        date_to,
        project_id,
    )
    by_task_type = await pool.fetch(
        """
        SELECT h."TaskType" AS task_type, COALESCE(SUM(h."Hours"), 0) AS total_hours
        FROM "ReportHoursBreakdowns" h
        JOIN "Reports" r ON r."Id" = h."ReportId"
        WHERE r."WeekStartDate" >= $1 AND r."WeekStartDate" <= $2
          AND ($3::uuid IS NULL OR r."ProjectId" = $3)
        GROUP BY h."TaskType"
        ORDER BY total_hours DESC
        """,
        date_from,
        date_to,
        project_id,
    )
    return {
        "by_project": [_row_to_dict(r) for r in by_project],
        "by_task_type_hours": [_row_to_dict(r) for r in by_task_type],
    }
