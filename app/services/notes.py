"""Note queries and changes."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Note


def list_notes(
    db: Session,
    *,
    project_id: int | None = None,
    unassigned: bool = False,
    q: str | None = None,
) -> list[Note]:
    stmt = (
        select(Note)
        .options(selectinload(Note.project))
        .order_by(Note.updated_at.desc(), Note.id.desc())
    )
    if project_id is not None:
        stmt = stmt.where(Note.project_id == project_id)
    elif unassigned:
        stmt = stmt.where(Note.project_id.is_(None))
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Note.title.ilike(pattern), Note.content.ilike(pattern)))
    return list(db.scalars(stmt))


def get_note(db: Session, note_id: int) -> Note | None:
    return db.get(Note, note_id)


def create_note(db: Session, data: dict) -> Note:
    note = Note(**data)
    db.add(note)
    db.commit()
    return note


def update_note(db: Session, note: Note, data: dict) -> Note:
    for key, value in data.items():
        setattr(note, key, value)
    db.commit()
    return note


def delete_note(db: Session, note: Note) -> None:
    db.delete(note)
    db.commit()
