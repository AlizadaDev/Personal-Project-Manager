"""Numbers and lists shown on the dashboard."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums import ProjectStatus, TaskStatus
from app.models import Project, Task
from app.services import projects as project_service
from app.services import tasks as task_service


@dataclass
class Dashboard:
    total_projects: int
    active_projects: int
    completed_projects: int
    pending_tasks: int
    today_tasks: list[Task]
    overdue_tasks: list[Task]
    recent_projects: list[Project]


def _count(db: Session, model, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0


def get_dashboard(db: Session, today: date | None = None) -> Dashboard:
    today = today or date.today()
    return Dashboard(
        total_projects=_count(db, Project),
        active_projects=_count(db, Project, Project.status == ProjectStatus.IN_PROGRESS),
        completed_projects=_count(db, Project, Project.status == ProjectStatus.COMPLETED),
        pending_tasks=_count(db, Task, Task.status != TaskStatus.DONE),
        today_tasks=task_service.list_tasks(db, open_only=True, due="today", today=today),
        overdue_tasks=task_service.list_tasks(db, due="overdue", today=today),
        recent_projects=project_service.list_projects(db, limit=5),
    )
