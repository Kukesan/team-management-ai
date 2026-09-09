import json
import logging
from datetime import date

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, InternalServerError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.errors import ToolExecutionError
from app.services.tools import TOOL_SCHEMAS, execute_tool

logger = logging.getLogger(__name__)

MAX_TOKENS = 1536

# Per-call budget for a single OpenAI request. Deliberately well under the SDK's 600s
# default and under team-management-api's outbound HttpClient.Timeout (see Program.cs) --
# a call that hangs this long is failing, not slow, so give up and let the retry/tool-loop
# logic below (or the caller) handle it rather than tying up the request indefinitely.
_REQUEST_TIMEOUT_SECONDS = 20.0

# Only retry errors that are plausibly transient (dropped connection, our own timeout above,
# rate limiting, a 5xx from OpenAI). A 4xx like BadRequestError/AuthenticationError will
# never succeed on retry, so failing immediately avoids burning the tool loop's iteration
# budget on a request that cannot work.
_RETRYABLE_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)

CHAT_SYSTEM_PROMPT = """You are an AI assistant embedded in a team weekly-report \
dashboard, answering a manager's questions about their team's activity. Today's \
date is {today}.

Rules:
- Answer ONLY using information returned by tool calls. Never invent tasks, \
blockers, achievements, hours, or people that a tool result didn't return.
- If a person or project name in the question is ambiguous, use list_projects / \
list_team_members to resolve it before querying report data.
- If tool results don't contain enough information to answer, say so plainly \
instead of guessing.
- Keep answers concise and reference specific people/projects/numbers from the \
tool results rather than vague generalities.
"""

SUMMARY_SYSTEM_PROMPT = """You are an AI assistant generating a weekly team-activity \
summary for a manager, from the structured report data provided below (already \
fetched -- do not assume any other data exists). Write a concise markdown summary \
with three sections: "Completed Work" (notable highlights), "Recurring / Unresolved \
Blockers" (call out anything appearing more than once or still unresolved), and \
"Workload Notes" (flag any imbalance visible in the hours/task-type data -- e.g. one \
person or project carrying disproportionate hours). Ground every statement in the \
provided data; do not fabricate details."""


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key, timeout=_REQUEST_TIMEOUT_SECONDS)


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(_RETRYABLE_ERRORS),
    reraise=True,
)
async def _create_completion(client: AsyncOpenAI, **kwargs):
    return await client.chat.completions.create(**kwargs)


async def run_tool_loop(user_message: str, history: list[dict], max_iterations: int = 6) -> dict:
    """Drives the tool-use loop for the chat endpoint. `history` is a list of
    {"role": "user"|"assistant", "content": str} turns from the caller. Returns
    {"answer": str, "tools_used": [str]}."""
    client = _client()
    model = get_settings().openai_model
    system = CHAT_SYSTEM_PROMPT.format(today=date.today().isoformat())

    messages: list[dict] = [{"role": "system", "content": system}]
    messages.extend({"role": h["role"], "content": h["content"]} for h in history)
    messages.append({"role": "user", "content": user_message})

    tools_used: list[str] = []

    for _ in range(max_iterations):
        response = await _create_completion(
            client,
            model=model,
            max_tokens=MAX_TOKENS,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return {"answer": message.content or "", "tools_used": tools_used}

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ],
            }
        )

        for tool_call in message.tool_calls:
            tools_used.append(tool_call.function.name)
            try:
                tool_input = json.loads(tool_call.function.arguments or "{}")
                result = await execute_tool(tool_call.function.name, tool_input)
                content = json.dumps(result)
            except ToolExecutionError as exc:
                content = str(exc)
            except Exception:
                logger.exception("Tool %s failed unexpectedly", tool_call.function.name)
                content = "Internal error executing this tool."
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": content,
                }
            )

    return {
        "answer": "I wasn't able to fully answer that within the allotted tool-call budget. "
        "Try narrowing the question (e.g. a specific project or week).",
        "tools_used": tools_used,
    }


async def summarize(week_start: str, reports: list[dict], submission_status: list[dict], workload: dict) -> str:
    client = _client()
    model = get_settings().openai_model

    data_blob = json.dumps(
        {
            "week_start": week_start,
            "reports": reports,
            "submission_status": submission_status,
            "workload": workload,
        },
        indent=2,
    )

    response = await _create_completion(
        client,
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": f"Report data:\n{data_blob}"},
        ],
    )
    return response.choices[0].message.content or ""
