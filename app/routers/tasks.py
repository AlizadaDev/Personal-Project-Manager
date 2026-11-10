from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import TaskPriority, TaskStatus
from app.models import Task
from app.services import projects as project_service
from app.services import tasks as task_service
from app.templating import redirect, render, safe_next
from app.validation import parse_filter, parse_project_filter, validate_task

router = APIRouter(prefix="/tasks", tags=["tasks"])

DB = Annotated[Session, Depends(get_db)]
FormStr = Annotated[str, Form()]


def task_form(
    title: FormStr = "",
    description: FormStr = "",
    project_id: FormStr = "",
    priority: FormStr = "",
    status: FormStr = "",
    due_date: FormStr = "",
) -> dict[str, str]:
    return {
        "title": title,
        "description": description,
        "project_id": project_id,
        "priority": priority,
        "status": status,
        "due_date": due_date,
    }


TaskForm = Annotated[dict[str, str], Depends(task_form)]


def _get_or_404(db: Session, task_id: int) -> Task:
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404)
    return task


def _values(task: Task) -> dict[str, str]:
    return {
        "title": task.title,
        "description": task.description,
        "project_id": str(task.project_id or ""),
        "priority": task.priority.value,
        "status": task.status.value,
        "due_date": task.due_date.isoformat() if task.due_date else "",
    }


def _render_form(request, db, values, next_url, errors=None, task=None, status_code=200):
    context = {
        "task": task,
        "values": values,
        "errors": errors or {},
        "projects": project_service.project_choices(db),
        "next_url": next_url,
    }
    return render(request, "tasks/form.html", context, status_code)


@router.get("")
def list_tasks(
    request: Request,
    db: DB,
    status: str = "",
    priority: str = "",
    project: str = "",
    due: str = "",
    q: str = "",
):
    project_id, unassigned = parse_project_filter(project)
    tasks = task_service.list_tasks(
        db,
        status=parse_filter(status, TaskStatus),
        open_only=status == "open",
        priority=parse_filter(priority, TaskPriority),
        project_id=project_id,
        unassigned=unassigned,
        due=due if due in task_service.DUE_FILTERS else None,
        q=q.strip() or None,
    )
    context = {
        "tasks": tasks,
        "projects": project_service.project_choices(db),
        "due_filters": task_service.DUE_FILTERS,
        "filters": {"status": status, "priority": priority, "project": project, "due": due, "q": q},
    }
    return render(request, "tasks/list.html", context)


@router.get("/new")
def new_task(request: Request, db: DB, project_id: str = "", next: str = ""):
    defaults = {
        "priority": TaskPriority.MEDIUM.value,
        "status": TaskStatus.TODO.value,
        "project_id": project_id,
    }
    return _render_form(request, db, defaults, safe_next(next, "/tasks"))


@router.post("")
def create_task(request: Request, db: DB, form: TaskForm, next: FormStr = ""):
    next_url = safe_next(next, "/tasks")
    data, errors = validate_task(form, db)
    if errors:
        return _render_form(request, db, form, next_url, errors, status_code=422)
    task_service.create_task(db, data)
    return redirect(next_url, "task_created")


@router.get("/{task_id}/edit")
def edit_task(request: Request, db: DB, task_id: int, next: str = ""):
    task = _get_or_404(db, task_id)
    return _render_form(request, db, _values(task), safe_next(next, "/tasks"), task=task)


@router.post("/{task_id}/edit")
def update_task(request: Request, db: DB, task_id: int, form: TaskForm, next: FormStr = ""):
    task = _get_or_404(db, task_id)
    next_url = safe_next(next, "/tasks")
    data, errors = validate_task(form, db)
    if errors:
        return _render_form(request, db, form, next_url, errors, task=task, status_code=422)
    task_service.update_task(db, task, data)
    return redirect(next_url, "task_updated")


@router.post("/{task_id}/toggle")
def toggle_task(db: DB, task_id: int, next: FormStr = ""):
    task_service.toggle_task(db, _get_or_404(db, task_id))
    return redirect(safe_next(next, "/tasks"))


@router.post("/{task_id}/delete")
def delete_task(db: DB, task_id: int, next: FormStr = ""):
    task_service.delete_task(db, _get_or_404(db, task_id))
    return redirect(safe_next(next, "/tasks"), "task_deleted")
