# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this service is

FastAPI backend that gives an OpenAI model read-only tool access to the `team-management-api`
Postgres database, to answer a manager's natural-language questions (`POST /chat`) and generate
AI weekly summaries (`POST /summary`). It stores no data of its own and is **never called from
the browser** — `team-management-api`'s `AiController` authenticates the real user (JWT,
Manager/Admin only) and forwards the request here with a shared internal secret.

## Commands

```
python -m venv .venv
.venv\Scripts\activate                          # Windows
pip install -r requirements.txt

cp .env.example .env                             # then fill in DATABASE_URL, OPENAI_API_KEY, INTERNAL_API_KEY

uvicorn app.main:app --reload --port 8001        # run the service
```

- Health check (no auth): `GET http://localhost:8001/health`
- Interactive docs (still requires `X-Internal-Api-Key`/`X-User-*` headers): `http://localhost:8001/docs`
- No test suite, linter, or formatter is configured in this repo yet.

`DATABASE_URL` must point at the same Supabase Postgres project `team-management-api`'s
`ConnectionStrings:DefaultConnection` uses. Prefer a dedicated read-only Postgres role (see
README.md for the `GRANT SELECT` snippet) over reusing the app's migration credentials.

## Architecture

**Request flow**: `team-management-api` (ASP.NET) → this service. Every router except
`/health` runs two dependencies in sequence:
1. `verify_internal_api_key` ([app/dependencies.py](app/dependencies.py)) — validates
   `X-Internal-Api-Key` against `INTERNAL_API_KEY`. This is the only thing that proves the
   caller is the trusted gateway, not a browser.
2. `get_current_context` — parses the already-authenticated identity forwarded via
   `X-User-Id`/`X-User-Name`/`X-User-Roles` headers, and as defense-in-depth (not solely
   relying on the gateway's `[Authorize(Roles=...)]`) rejects any request whose roles don't
   include Manager or Admin.

**Layering**: `routers/` (HTTP I/O, Pydantic request/response models in `schemas/`) →
`services/llm.py` (OpenAI tool-calling loop) → `services/tools.py` (tool schemas + dispatch) →
`repositories/reports_repository.py` (parameterized SQL) → `db/pool.py` (asyncpg pool,
created/closed in the `main.py` lifespan).

**Tool-calling loop** (`services/llm.py::run_tool_loop`): drives up to `max_iterations` rounds
of `chat.completions.create(tools=TOOL_SCHEMAS)`, executing each requested tool via
`services/tools.py::execute_tool` and feeding the JSON result back as a `role: "tool"` message,
until the model responds without further tool calls. `summarize()` is a single non-agentic call
that receives pre-fetched report/submission/workload data and writes a markdown summary — the
router (`routers/summary.py`), not the model, decides what data to fetch. System prompts for
both instruct the model to ground every statement in tool/data results and never fabricate.

**Database access is read-only and schema-borrowed**: `team-management-api` (EF Core) owns and
migrates the schema; this service only issues `SELECT`s against it. EF Core here uses no
snake_case convention or `ToTable()` overrides, so every SQL identifier is the literal
PascalCase C# name and must be double-quoted (e.g. `"Reports"`, `"WeekStartDate"`). Every enum
column is stored via `HasConversion<string>()`, so filters/results are the literal C# enum
member text (`"NeedsCorrection"`, `"InProgress"`, ...), not integers. `db/pool.py` registers
`json`/`jsonb` type codecs so `json_agg()`/`json_build_object()` results decode to Python
lists/dicts instead of raw text; `repositories/reports_repository.py::_clean` recursively
normalizes `UUID`/`date`/`Decimal` values from asyncpg into JSON-serializable types before
returning rows (used both for tool results sent to the model and for HTTP responses).

**Config** (`config.py`): a single `pydantic-settings` `Settings`, loaded from `.env`, fails
fast on first access if a required value is missing — mirrors `team-management-api`'s
`?? throw new InvalidOperationException(...)` pattern on `Jwt:Key`.

**Adding a new tool**: add its OpenAI function schema to `TOOL_SCHEMAS` and a branch in
`execute_tool` in [app/services/tools.py](app/services/tools.py), and the underlying query to
[app/repositories/reports_repository.py](app/repositories/reports_repository.py). Tools must
stay read-only and raise `ToolExecutionError` (not a generic exception) for invalid input so the
loop reports it back to the model instead of failing the whole request.
