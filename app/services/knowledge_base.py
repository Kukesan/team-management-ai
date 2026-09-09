from functools import lru_cache
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"

# Which markdown file(s) a role's content lives in, on top of common.md. Each role
# also inherits the files of the roles beneath it (Admin can do everything a Manager
# and TeamMember can, Manager everything a TeamMember can -- mirrors the app's actual
# permission hierarchy, and what admin.md/manager.md themselves claim in prose).
# Keys must match team-management-api's Domain.Constants.Roles values, forwarded
# verbatim in the X-User-Roles header.
ROLE_FILES = {
    "TeamMember": ["team-member.md"],
    "Manager": ["team-member.md", "manager.md"],
    "Admin": ["team-member.md", "manager.md", "admin.md"],
}


@lru_cache(maxsize=None)
def _read_kb_file(filename: str) -> str:
    path = KB_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_knowledge_base(roles: list[str]) -> str:
    """Combines common.md with the markdown file(s) for each of the caller's roles,
    so the help assistant only ever sees how-to content for what that role can
    actually do in the app (e.g. an Employee never sees "how to create a project")."""
    sections = [_read_kb_file("common.md")]
    seen_files: set[str] = set()
    for role in roles:
        for filename in ROLE_FILES.get(role, []):
            if filename not in seen_files:
                seen_files.add(filename)
                content = _read_kb_file(filename)
                if content:
                    sections.append(content)
    return "\n\n".join(section for section in sections if section)
