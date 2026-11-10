from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ProjectCategory, ProjectStatus
from app.models import Project
from app.services import notes as note_service
from app.services import projects as project_service
from app.services import tasks as task_service
from app.templating import redirect, render
from app.validation import parse_filter, validate_project

router = APIRouter(prefix="/projects", tags=["projects"])

DB = Annotated[Session, Depends(get_db)]
FormStr = Annotated[str, Form()]


def project_form(
    name: FormStr = "",
    description: FormStr = "",
    category: FormStr = "",
    status: FormStr = "",
    start_date: FormStr = "",
    deadline: FormStr = "",
) -> dict[str, str]:
    return {
        "name": name,
        "description": description,
        "category": category,
        "status": status,
        "start_date": start_date,
        "deadline": deadline,
    }


ProjectForm = Annotated[dict[str, str], Depends(project_form)]


def _get_or_404(db: Session, project_id: int) -> Project:
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404)
    return project


def _values(project: Project) -> dict[str, str]:
    return {
        "name": project.name,
        "description": project.description,
        "category": project.category.value,
        "status": project.status.value,
        "start_date": project.start_date.isoformat() if project.start_date else "",
        "deadline": project.deadline.isoformat() if project.deadline else "",
    }


def _render_form(request, values, errors=None, project=None, status_code=200):
    context = {"project": project, "values": values, "errors": errors or {}}
    return render(request, "projects/form.html", context, status_code)


@router.get("")
def list_projects(request: Request, db: DB, status: str = "", category: str = "", q: str = ""):
    projects = project_service.list_projects(
        db,
        status=parse_filter(status, ProjectStatus),
        category=parse_filter(category, ProjectCategory),
        q=q.strip() or None,
    )
    context = {
        "projects": projects,
        "progress": project_service.task_progress(db),
        "filters": {"status": status, "category": category, "q": q},
    }
    return render(request, "projects/list.html", context)


@router.get("/new")
def new_project(request: Request):
    defaults = {"status": ProjectStatus.PLANNING.value, "category": ProjectCategory.OTHER.value}
    return _render_form(request, defaults)


@router.post("")
def create_project(request: Request, db: DB, form: ProjectForm):
    data, errors = validate_project(form)
    if errors:
        return _render_form(request, form, errors, status_code=422)
    project = project_service.create_project(db, data)
    return redirect(f"/projects/{project.id}", "project_created")


@router.get("/{project_id}")
def project_detail(request: Request, db: DB, project_id: int):
    project = _get_or_404(db, project_id)
    tasks = task_service.list_tasks(db, project_id=project_id)
    context = {
        "project": project,
        "tasks": tasks,
        "done_count": sum(task.is_done for task in tasks),
        "notes": note_service.list_notes(db, project_id=project_id),
    }
    return render(request, "projects/detail.html", context)


@router.get("/{project_id}/edit")
def edit_project(request: Request, db: DB, project_id: int):
    project = _get_or_404(db, project_id)
    return _render_form(request, _values(project), project=project)


@router.post("/{project_id}/edit")
def update_project(request: Request, db: DB, project_id: int, form: ProjectForm):
    project = _get_or_404(db, project_id)
    data, errors = validate_project(form)
    if errors:
        return _render_form(request, form, errors, project=project, status_code=422)
    project_service.update_project(db, project, data)
    return redirect(f"/projects/{project.id}", "project_updated")


@router.post("/{project_id}/delete")
def delete_project(db: DB, project_id: int):
    project_service.delete_project(db, _get_or_404(db, project_id))
    return redirect("/projects", "project_deleted")
