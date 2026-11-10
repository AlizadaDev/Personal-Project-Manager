from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Note
from app.services import notes as note_service
from app.services import projects as project_service
from app.templating import redirect, render, safe_next
from app.validation import parse_project_filter, validate_note

router = APIRouter(prefix="/notes", tags=["notes"])

DB = Annotated[Session, Depends(get_db)]
FormStr = Annotated[str, Form()]


def note_form(title: FormStr = "", content: FormStr = "", project_id: FormStr = "") -> dict[str, str]:
    return {"title": title, "content": content, "project_id": project_id}


NoteForm = Annotated[dict[str, str], Depends(note_form)]


def _get_or_404(db: Session, note_id: int) -> Note:
    note = note_service.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404)
    return note


def _values(note: Note) -> dict[str, str]:
    return {"title": note.title, "content": note.content, "project_id": str(note.project_id or "")}


def _render_form(request, db, values, cancel_url, next_url="", errors=None, note=None, status_code=200):
    context = {
        "note": note,
        "values": values,
        "errors": errors or {},
        "projects": project_service.project_choices(db),
        "next_url": next_url,
        "cancel_url": cancel_url,
    }
    return render(request, "notes/form.html", context, status_code)


@router.get("")
def list_notes(request: Request, db: DB, project: str = "", q: str = ""):
    project_id, unassigned = parse_project_filter(project)
    notes = note_service.list_notes(
        db, project_id=project_id, unassigned=unassigned, q=q.strip() or None
    )
    context = {
        "notes": notes,
        "projects": project_service.project_choices(db),
        "filters": {"project": project, "q": q},
    }
    return render(request, "notes/list.html", context)


@router.get("/new")
def new_note(request: Request, db: DB, project_id: str = "", next: str = ""):
    next_url = safe_next(next, "")
    return _render_form(request, db, {"project_id": project_id}, next_url or "/notes", next_url)


@router.post("")
def create_note(request: Request, db: DB, form: NoteForm, next: FormStr = ""):
    next_url = safe_next(next, "")
    data, errors = validate_note(form, db)
    if errors:
        return _render_form(
            request, db, form, next_url or "/notes", next_url, errors, status_code=422
        )
    note = note_service.create_note(db, data)
    return redirect(next_url or f"/notes/{note.id}", "note_created")


@router.get("/{note_id}")
def note_detail(request: Request, db: DB, note_id: int):
    return render(request, "notes/detail.html", {"note": _get_or_404(db, note_id)})


@router.get("/{note_id}/edit")
def edit_note(request: Request, db: DB, note_id: int):
    note = _get_or_404(db, note_id)
    return _render_form(request, db, _values(note), f"/notes/{note.id}", note=note)


@router.post("/{note_id}/edit")
def update_note(request: Request, db: DB, note_id: int, form: NoteForm):
    note = _get_or_404(db, note_id)
    data, errors = validate_note(form, db)
    if errors:
        return _render_form(
            request, db, form, f"/notes/{note.id}", errors=errors, note=note, status_code=422
        )
    note_service.update_note(db, note, data)
    return redirect(f"/notes/{note.id}", "note_updated")


@router.post("/{note_id}/delete")
def delete_note(db: DB, note_id: int, next: FormStr = ""):
    note_service.delete_note(db, _get_or_404(db, note_id))
    return redirect(safe_next(next, "/notes"), "note_deleted")
