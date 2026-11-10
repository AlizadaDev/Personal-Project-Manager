"""Project queries and changes."""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.enums import ProjectCategory, ProjectStatus, TaskStatus
from app.models import Project, Task


def list_projects(
    db: Session,
    *,
    status: ProjectStatus | None = None,
    category: ProjectCategory | None = None,
    q: str | None = None,
    limit: int | None = None,
) -> list[Project]:
    stmt = select(Project).order_by(Project.updated_at.desc(), Project.id.desc()).limit(limit)
    if status:
        stmt = stmt.where(Project.status == status)
    if category:
        stmt = stmt.where(Project.category == category)
    if q:
        stmt = stmt.where(Project.name.ilike(f"%{q}%"))
    return list(db.scalars(stmt))


def project_choices(db: Session) -> list[Project]:
    """All projects ordered by name, for the project dropdown in task/note forms."""
    return list(db.scalars(select(Project).order_by(Project.name)))


def get_project(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def create_project(db: Session, data: dict) -> Project:
    project = Project(**data)
    db.add(project)
    db.commit()
    return project


def update_project(db: Session, project: Project, data: dict) -> Project:
    for key, value in data.items():
        setattr(project, key, value)
    db.commit()
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()


def task_progress(db: Session) -> dict[int, tuple[int, int]]:
    """Map project id -> (done tasks, total tasks)."""
    done = func.sum(case((Task.status == TaskStatus.DONE, 1), else_=0))
    rows = db.execute(
        select(Task.project_id, done, func.count(Task.id))
        .where(Task.project_id.is_not(None))
        .group_by(Task.project_id)
    )
    return {project_id: (int(done_count or 0), total) for project_id, done_count, total in rows}
