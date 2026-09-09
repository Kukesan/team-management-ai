from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

MAX_TOKENS = 1024

HELP_SYSTEM_PROMPT = """You are an in-app help assistant for this team management app, \
answering "how do I..." questions about using the product itself (navigation, \
features, workflows). You have NO access to the database or any user's real data -- \
you only know the product documentation below, which has already been filtered to \
what this user's role can do.

Rules:
- Answer ONLY using the documentation provided below. If it doesn't cover something, \
say you don't know and suggest contacting an admin/support instead of guessing.
- Never claim to see or fetch the user's actual projects, reports, or teammates -- \
you have no access to real data, only how-to guidance.
- If the user asks about a feature not covered in the documentation below, say so \
plainly rather than describing how to use it -- it likely isn't available for their role.
- Keep answers concise and actionable, ideally as short numbered steps.

Documentation:
{knowledge_base}
"""


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _create_completion(client: AsyncOpenAI, **kwargs):
    return await client.chat.completions.create(**kwargs)


async def answer_help_question(user_message: str, history: list[dict], knowledge_base: str) -> str:
    """Single non-agentic call (no tools, no DB access) that answers a how-to
    question purely from the role-filtered knowledge base markdown."""
    client = _client()
    model = get_settings().openai_model
    system = HELP_SYSTEM_PROMPT.format(knowledge_base=knowledge_base)

    messages: list[dict] = [{"role": "system", "content": system}]
    messages.extend({"role": h["role"], "content": h["content"]} for h in history)
    messages.append({"role": "user", "content": user_message})

    response = await _create_completion(client, model=model, max_tokens=MAX_TOKENS, messages=messages)
    return response.choices[0].message.content or ""
