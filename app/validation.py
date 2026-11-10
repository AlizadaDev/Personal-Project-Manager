"""Form validation. Each validator turns raw form strings into typed data plus an errors dict.

If ``errors`` is empty the data is safe to pass to a service function.
"""

from datetime import date
from enum import StrEnum
from typing import TypeVar

from sqlalchemy.orm import Session

from app.enums import ProjectCategory, ProjectStatus, TaskPriority, TaskStatus
from app.models import Project

Errors = dict[str, str]
E = TypeVar("E", bound=StrEnum)


def clean(value: str | None) -> str:
    return (value or "").strip()


def parse_filter(raw: str | None, enum_cls: type[E]) -> E | None:
    """Lenient enum parsing for list filters: unknown values simply mean "no filter"."""
    try:
        return enum_cls(clean(raw))
    except ValueError:
        return None


def parse_project_filter(raw: str | None) -> tuple[int | None, bool]:
    """List filter for the project dropdown: an id, "none" (no project) or empty (all).

    Returns (project_id, unassigned_only).
    """
    value = clean(raw)
    if value == "none":
        return None, True
    return (int(value) if value.isdigit() else None), False


def _required_text(raw: str | None, field: str, max_len: int, errors: Errors) -> str:
    value = clean(raw)
    if not value:
        errors[field] = "This field is required."
    elif len(value) > max_len:
        errors[field] = f"Keep it under {max_len} characters."
    return value


def _enum(raw: str | None, enum_cls: type[E], field: str, errors: Errors) -> E | None:
    try:
        return enum_cls(clean(raw))
    except ValueError:
        errors[field] = "Choose a valid option."
        return None


def _date(raw: str | None, field: str, errors: Errors) -> date | None:
    value = clean(raw)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors[field] = "Enter a valid date."
        return None


def _project_ref(raw: str | None, db: Session, errors: Errors) -> int | None:
    value = clean(raw)
    if not value:
        return None
    if not value.isdigit() or db.get(Project, int(value)) is None:
        errors["project_id"] = "Choose a valid project."
        return None
    return int(value)


def validate_project(form: dict[str, str]) -> tuple[dict, Errors]:
    errors: Errors = {}
    data = {
        "name": _required_text(form.get("name"), "name", 150, errors),
        "description": clean(form.get("description")),
        "category": _enum(form.get("category"), ProjectCategory, "category", errors),
        "status": _enum(form.get("status"), ProjectStatus, "status", errors),
        "start_date": _date(form.get("start_date"), "start_date", errors),
        "deadline": _date(form.get("deadline"), "deadline", errors),
    }
    if data["start_date"] and data["deadline"] and data["deadline"] < data["start_date"]:
        errors["deadline"] = "Deadline can't be before the start date."
    return data, errors


def validate_task(form: dict[str, str], db: Session) -> tuple[dict, Errors]:
    errors: Errors = {}
    data = {
        "title": _required_text(form.get("title"), "title", 200, errors),
        "description": clean(form.get("description")),
        "project_id": _project_ref(form.get("project_id"), db, errors),
        "priority": _enum(form.get("priority"), TaskPriority, "priority", errors),
        "status": _enum(form.get("status"), TaskStatus, "status", errors),
        "due_date": _date(form.get("due_date"), "due_date", errors),
    }
    return data, errors


def validate_note(form: dict[str, str], db: Session) -> tuple[dict, Errors]:
    errors: Errors = {}
    data = {
        "title": _required_text(form.get("title"), "title", 200, errors),
        "content": clean(form.get("content")),
        "project_id": _project_ref(form.get("project_id"), db, errors),
    }
    return data, errors
