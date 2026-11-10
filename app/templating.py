"""Jinja2 setup plus small helpers shared by all routers (render, redirect, flash messages)."""

from datetime import date, datetime
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import APP_DIR, APP_NAME
from app.enums import ProjectCategory, ProjectStatus, TaskPriority, TaskStatus

templates = Jinja2Templates(directory=APP_DIR / "templates")

FLASH_MESSAGES = {
    "project_created": "Project created.",
    "project_updated": "Project updated.",
    "project_deleted": "Project deleted.",
    "task_created": "Task created.",
    "task_updated": "Task updated.",
    "task_deleted": "Task deleted.",
    "note_created": "Note created.",
    "note_updated": "Note updated.",
    "note_deleted": "Note deleted.",
}


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return templates.TemplateResponse(request, name, context or {}, status_code=status_code)


def redirect(url: str, msg: str | None = None) -> RedirectResponse:
    """303 redirect after a POST (Post/Redirect/GET), optionally carrying a flash message key."""
    if msg:
        url = f"{url}{'&' if '?' in url else '?'}msg={msg}"
    return RedirectResponse(url, status_code=303)


def safe_next(raw: str | None, default: str) -> str:
    """Only allow redirects to local paths, never to another site."""
    if raw and raw.startswith("/") and not raw.startswith("//") and "\\" not in raw:
        return raw
    return default


# ---- template globals -------------------------------------------------------------------


def current_url(request: Request) -> str:
    """Current path + query string without the one-off ``msg`` flash parameter."""
    params = [(k, v) for k, v in request.query_params.multi_items() if k != "msg"]
    return request.url.path + (f"?{urlencode(params)}" if params else "")


def flash_message(request: Request) -> str | None:
    return FLASH_MESSAGES.get(request.query_params.get("msg", ""))


def static_url(path: str) -> str:
    """URL for a static file with a version tag, so browsers fetch it again after it changes."""
    try:
        version = int((APP_DIR / "static" / path).stat().st_mtime)
    except OSError:
        version = 0
    return f"/static/{path}?v={version}"


def enum_options(enum_cls) -> list[tuple[str, str]]:
    return [(member.value, member.value) for member in enum_cls]


def project_options(projects) -> list[tuple[int, str]]:
    return [(project.id, project.name) for project in projects]


# ---- template filters -------------------------------------------------------------------


def slug(value) -> str:
    return str(value).lower().replace(" ", "-")


def fmt_date(value: date | datetime | None) -> str:
    return value.strftime("%d %b %Y") if value else "—"


def fmt_datetime(value: datetime | None) -> str:
    return value.strftime("%d %b %Y, %H:%M") if value else "—"


def due_label(value: date | None) -> str:
    if not value:
        return "No due date"
    today = date.today()
    labels = {0: "Today", 1: "Tomorrow", -1: "Yesterday"}
    delta = (value - today).days
    if delta in labels:
        return labels[delta]
    return value.strftime("%d %b") if value.year == today.year else fmt_date(value)


# Inline SVG icon paths (24x24, stroke-based) so no icon library is needed.
ICONS = {
    "logo": '<path d="m12 2 10 5-10 5L2 7Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "dashboard": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "folder": '<path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.7-.9l-.8-1.2A2 2 0 0 0 7.9 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "tasks": '<path d="m9 11 3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    "note": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "menu": '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.9 4.9 1.4 1.4"/><path d="m17.7 17.7 1.4 1.4"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.3 17.7-1.4 1.4"/><path d="m19.1 4.9-1.4 1.4"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "edit": '<path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "back": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    "play": '<circle cx="12" cy="12" r="10"/><path d="m10 8 6 4-6 4Z"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "list": '<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>',
    "alert": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
}

templates.env.globals.update(
    app_name=APP_NAME,
    ICONS=ICONS,
    today=date.today,
    current_url=current_url,
    static_url=static_url,
    flash_message=flash_message,
    enum_options=enum_options,
    project_options=project_options,
    ProjectStatus=ProjectStatus,
    ProjectCategory=ProjectCategory,
    TaskStatus=TaskStatus,
    TaskPriority=TaskPriority,
)
templates.env.filters.update(
    slug=slug, fmt_date=fmt_date, fmt_datetime=fmt_datetime, due_label=due_label
)
