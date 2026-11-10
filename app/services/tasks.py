"""Task queries and changes."""

from datetime import date, datetime, timedelta

from sqlalchemy import case, select
from sqlalchemy.orm import Session, selectinload

from app.enums import TaskPriority, TaskStatus
from app.models import Task

# Open tasks first, then by due date (no date last), then High -> Low priority.
_DEFAULT_ORDER = (
    case((Task.status == TaskStatus.DONE, 1), else_=0),
    Task.due_date.is_(None),
    Task.due_date,
    case((Task.priority == TaskPriority.HIGH, 0), (Task.priority == TaskPriority.MEDIUM, 1), else_=2),
    Task.created_at.desc(),
)

DUE_FILTERS = {"overdue": "Overdue", "today": "Due today", "week": "Next 7 days"}


def list_tasks(
    db: Session,
    *,
    status: TaskStatus | None = None,
    open_only: bool = False,
    priority: TaskPriority | None = None,
    project_id: int | None = None,
    unassigned: bool = False,
    due: str | None = None,
    q: str | None = None,
    today: date | None = None,
) -> list[Task]:
    today = today or date.today()
    stmt = select(Task).options(selectinload(Task.project)).order_by(*_DEFAULT_ORDER)

    if status:
        stmt = stmt.where(Task.status == status)
    elif open_only:
        stmt = stmt.where(Task.status != TaskStatus.DONE)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    elif unassigned:
        stmt = stmt.where(Task.project_id.is_(None))
    if due == "today":
        stmt = stmt.where(Task.due_date == today)
    elif due == "overdue":
        stmt = stmt.where(Task.due_date < today, Task.status != TaskStatus.DONE)
    elif due == "week":
        stmt = stmt.where(Task.due_date.between(today, today + timedelta(days=6)))
    if q:
        stmt = stmt.where(Task.title.ilike(f"%{q}%"))
    return list(db.scalars(stmt))


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def _set_status(task: Task, status: TaskStatus) -> None:
    if status == TaskStatus.DONE:
        if task.status != TaskStatus.DONE or task.completed_at is None:
            task.completed_at = datetime.now()
    else:
        task.completed_at = None
    task.status = status


def _apply(task: Task, data: dict) -> None:
    for key, value in data.items():
        if key == "status":
            _set_status(task, value)
        else:
            setattr(task, key, value)


def create_task(db: Session, data: dict) -> Task:
    task = Task()
    _apply(task, data)
    db.add(task)
    db.commit()
    return task


def update_task(db: Session, task: Task, data: dict) -> Task:
    _apply(task, data)
    db.commit()
    return task


def toggle_task(db: Session, task: Task) -> Task:
    _set_status(task, TaskStatus.TODO if task.is_done else TaskStatus.DONE)
    db.commit()
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
