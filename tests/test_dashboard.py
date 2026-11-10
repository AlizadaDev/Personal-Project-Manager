from datetime import date, timedelta

import pytest

from app.enums import ProjectStatus, TaskStatus
from app.services import projects as project_service
from app.services import tasks as task_service
from app.services.dashboard import get_dashboard

TODAY = date(2026, 11, 10)


def test_dashboard_numbers(db):
    project_service.create_project(db, {"name": "A", "status": ProjectStatus.IN_PROGRESS})
    project_service.create_project(db, {"name": "B", "status": ProjectStatus.IN_PROGRESS})
    project_service.create_project(db, {"name": "C", "status": ProjectStatus.COMPLETED})
    project_service.create_project(db, {"name": "D", "status": ProjectStatus.PLANNING})

    task_service.create_task(db, {"title": "today open", "due_date": TODAY})
    task_service.create_task(db, {"title": "today done", "due_date": TODAY, "status": TaskStatus.DONE})
    task_service.create_task(db, {"title": "overdue", "due_date": TODAY - timedelta(days=1)})
    task_service.create_task(db, {"title": "later", "due_date": TODAY + timedelta(days=3)})

    d = get_dashboard(db, today=TODAY)

    assert d.total_projects == 4
    assert d.active_projects == 2
    assert d.completed_projects == 1
    assert d.pending_tasks == 3
    assert [t.title for t in d.today_tasks] == ["today open"]
    assert [t.title for t in d.overdue_tasks] == ["overdue"]
    assert len(d.recent_projects) == 4


def test_recent_projects_limited_to_five(db):
    for i in range(7):
        project_service.create_project(db, {"name": f"P{i}"})
    assert len(get_dashboard(db).recent_projects) == 5


def test_dashboard_page_renders(client, db):
    project_service.create_project(db, {"name": "Agency site", "status": ProjectStatus.IN_PROGRESS})
    task_service.create_task(db, {"title": "Call client", "due_date": date.today()})

    page = client.get("/")
    assert page.status_code == 200
    assert "Agency site" in page.text
    assert "Call client" in page.text


@pytest.mark.parametrize(
    "url", ["/", "/projects", "/projects/new", "/tasks", "/tasks/new", "/notes", "/notes/new"]
)
def test_pages_render_when_empty(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert "<html" in response.text


def test_static_assets_are_served(client):
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200
