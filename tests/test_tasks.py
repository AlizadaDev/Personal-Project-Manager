from datetime import date, timedelta

from app.enums import TaskPriority, TaskStatus
from app.models import Task
from app.services import projects as project_service
from app.services import tasks as task_service
from tests.conftest import task_form


def test_create_task_assigned_to_project(client, db):
    project = project_service.create_project(db, {"name": "Chatbot"})

    response = client.post(
        "/tasks", data=task_form(project_id=str(project.id), due_date="2026-11-20"), follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/tasks?msg=task_created"
    task = db.get(Task, 1)
    assert task.project_id == project.id
    assert task.priority == TaskPriority.HIGH
    assert task.due_date == date(2026, 11, 20)
    assert "Design homepage" in client.get(f"/projects/{project.id}").text


def test_create_task_returns_to_next_url(client, db):
    project = project_service.create_project(db, {"name": "Chatbot"})
    response = client.post(
        "/tasks",
        data={**task_form(project_id=str(project.id)), "next": f"/projects/{project.id}"},
        follow_redirects=False,
    )
    assert response.headers["location"] == f"/projects/{project.id}?msg=task_created"


def test_external_next_url_is_ignored(client):
    for evil in ("https://evil.example", "//evil.example", "/\\evil.example"):
        response = client.post("/tasks", data={**task_form(), "next": evil}, follow_redirects=False)
        assert response.headers["location"] == "/tasks?msg=task_created"


def test_invalid_project_and_date_are_rejected(client, db):
    response = client.post("/tasks", data=task_form(project_id="42", due_date="not-a-date"))

    assert response.status_code == 422
    assert "Choose a valid project." in response.text
    assert "Enter a valid date." in response.text
    assert db.query(Task).count() == 0


def test_completed_at_follows_status(db):
    task = task_service.create_task(db, {"title": "Ship it", "status": TaskStatus.DONE})
    assert task.completed_at is not None

    task_service.update_task(db, task, {"status": TaskStatus.IN_PROGRESS})
    assert task.completed_at is None


def test_toggle_marks_done_and_back(client, db):
    task = task_service.create_task(db, {"title": "Write copy"})

    response = client.post(f"/tasks/{task.id}/toggle", data={"next": "/"}, follow_redirects=False)
    assert response.headers["location"] == "/"
    db.expunge_all()
    task = db.get(Task, task.id)
    assert task.status == TaskStatus.DONE and task.completed_at is not None

    client.post(f"/tasks/{task.id}/toggle")
    db.expunge_all()
    task = db.get(Task, task.id)
    assert task.status == TaskStatus.TODO and task.completed_at is None


def test_edit_and_delete_task(client, db):
    task = task_service.create_task(db, {"title": "Old title"})

    assert 'value="Old title"' in client.get(f"/tasks/{task.id}/edit").text
    client.post(f"/tasks/{task.id}/edit", data=task_form(title="New title", status="In Progress"))
    db.expunge_all()
    assert db.get(Task, task.id).title == "New title"

    response = client.post(f"/tasks/{task.id}/delete", follow_redirects=False)
    assert response.headers["location"] == "/tasks?msg=task_deleted"
    db.expunge_all()
    assert db.get(Task, task.id) is None


def test_list_filters(client, db):
    today = date.today()
    task_service.create_task(db, {"title": "Due today task", "due_date": today})
    task_service.create_task(db, {"title": "Late task", "due_date": today - timedelta(days=2)})
    task_service.create_task(db, {"title": "Finished task", "status": TaskStatus.DONE})
    task_service.create_task(db, {"title": "Low task", "priority": TaskPriority.LOW})

    def titles(**params):
        text = client.get("/tasks", params=params).text
        return {t for t in ("Due today task", "Late task", "Finished task", "Low task") if t in text}

    assert titles(due="today") == {"Due today task"}
    assert titles(due="overdue") == {"Late task"}
    assert titles(status="open") == {"Due today task", "Late task", "Low task"}
    assert titles(status="Done") == {"Finished task"}
    assert titles(priority="Low") == {"Low task"}
    assert titles(q="late") == {"Late task"}


def test_open_tasks_are_listed_before_done_ones(db):
    task_service.create_task(db, {"title": "done", "status": TaskStatus.DONE})
    task_service.create_task(db, {"title": "open"})
    assert [t.title for t in task_service.list_tasks(db)] == ["open", "done"]
