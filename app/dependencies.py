import secrets
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.config import get_settings


async def verify_internal_api_key(x_internal_api_key: str = Header(...)) -> None:
    """Every router except /health depends on this. FastAPI is never reachable from
    the browser -- it trusts only team-management-api's AiService, which authenticates
    the real end user via its own JWT [Authorize] before forwarding a call here."""
    settings = get_settings()
    if not secrets.compare_digest(x_internal_api_key, settings.internal_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal API key.")


@dataclass
class RequestContext:
    user_id: str
    user_name: str
    roles: list[str]


async def get_current_context(
    x_user_id: str = Header(...),
    x_user_name: str = Header(...),
    x_user_roles: str = Header(default=""),
) -> RequestContext:
    """Parses the identity the gateway already authenticated -- not itself an auth
    check. Chat/summary are manager-facing per the assignment, so as defense in depth
    (not solely relying on AiController's [Authorize(Roles=...)]) this also rejects
    callers whose forwarded roles don't include Manager/Admin."""
    roles = [r.strip() for r in x_user_roles.split(",") if r.strip()]
    if not ({"Manager", "Admin"} & set(roles)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager or Admin role required.")
    return RequestContext(user_id=x_user_id, user_name=x_user_name, roles=roles)
