# team-management-ai

AI Chat Assistant backend for the Weekly Report Generator & Team Dashboard app.
Answers a manager's natural-language questions about team activity and generates
AI team summaries, by giving the OpenAI model a small set of read-only tools over the app's
existing report data. It does **not** store any data of its own — it reads directly
from the same Postgres database `team-management-api` writes to.

Never called by the browser directly: `team-management-api` is the gateway. Its
`AiController` authenticates the real user (JWT, Manager/Admin only) and forwards
the request here with a shared internal secret.

## Scope

Implements `POST /chat` (conversational Q&A) and `POST /summary` (AI-generated
weekly summary: completed work, recurring blockers, workload notes). Does not
implement document upload/RAG, persisted chat history, or the frontend chat
widget — those are future work.

## Prerequisites

- Python 3.11+
- The same Postgres database `team-management-api` uses (a Supabase Postgres
  project), reachable from this service
- An OpenAI API key

## Setup

1. Create and activate a virtualenv:
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS/Linux
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in `DATABASE_URL`, `OPENAI_API_KEY`,
   `INTERNAL_API_KEY` (any long random string — it must match the value configured
   on the `team-management-api` side, see below).

   **Recommended**: instead of pointing `DATABASE_URL` at the same credentials EF
   Core migrations use, create a dedicated read-only Postgres role for this service,
   since it should never write:
   ```sql
   create role ai_service_readonly login password '...';
   grant usage on schema public to ai_service_readonly;
   grant select on all tables in schema public to ai_service_readonly;
   alter default privileges in schema public grant select on tables to ai_service_readonly;
   ```
   Then use that role's credentials in `DATABASE_URL`.

## Running

```
uvicorn app.main:app --reload --port 8001
```

Health check: `GET http://localhost:8001/health` (no auth required).

Interactive API docs (still protected by `X-Internal-Api-Key`/`X-User-*` headers
on every non-health request): `http://localhost:8001/docs`.

## Wiring into team-management-api

In `team-management-api`, set (via `dotnet user-secrets` in Development, or
`AiService__BaseUrl` / `AiService__InternalApiKey` env vars elsewhere):

```
dotnet user-secrets set "AiService:BaseUrl" "http://localhost:8001"
dotnet user-secrets set "AiService:InternalApiKey" "<same value as INTERNAL_API_KEY above>"
```

`team-management-api`'s own `ConnectionStrings:DefaultConnection` must point at
the same Supabase Postgres project as this service's `DATABASE_URL` — both
services read/write the same database.

## Notes on data privacy

- `/chat` and `/summary` are Manager/Admin-only (enforced both by
  `team-management-api`'s `[Authorize(Roles=...)]` and, as defense in depth, by
  this service rejecting any forwarded identity whose roles don't include
  Manager/Admin).
- Only read (`SELECT`) queries are issued against the app database — see
  `app/repositories/reports_repository.py`.
- Report content sent to the OpenAI API is limited to what the manager's question
  actually needs (via tool calls), not a full data dump.
- The Supabase service-role/database credentials and the OpenAI API key live
  only in this service's environment — never returned in a response, never
  logged, `.env` is gitignored.
