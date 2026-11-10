from app.enums import ProjectCategory, ProjectStatus
from app.models import Note, Project, Task
from app.services import notes as note_service
from app.services import projects as project_service
from app.services import tasks as task_service
from tests.conftest import project_form


def test_create_project_redirects_to_detail(client, db):
    response = client.post("/projects", data=project_form(), follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/projects/1?msg=project_created"
    project = db.get(Project, 1)
    assert project.name == "Restaurant website"
    assert project.category == ProjectCategory.WEB_DEVELOPMENT
    assert project.status == ProjectStatus.IN_PROGRESS

    page = client.get(response.headers["location"])
    assert page.status_code == 200
    assert "Restaurant website" in page.text
    assert "Project created." in page.text


def test_project_name_is_required(client, db):
    response = client.post("/projects", data=project_form(name="   "))

    assert response.status_code == 422
    assert "This field is required." in response.text
    assert db.query(Project).count() == 0


def test_deadline_cannot_be_before_start_date(client):
    response = client.post("/projects", data=project_form(start_date="2026-12-10", deadline="2026-12-01"))

    assert response.status_code == 422
    assert "Deadline can&#39;t be before the start date." in response.text
    # Typed values are kept in the re-rendered form.
    assert 'value="Restaurant website"' in response.text


def test_invalid_category_is_rejected(client):
    response = client.post("/projects", data=project_form(category="Space Travel"))
    assert response.status_code == 422
    assert "Choose a valid option." in response.text


def test_edit_project(client, db):
    client.post("/projects", data=project_form())

    form_page = client.get("/projects/1/edit")
    assert form_page.status_code == 200
    assert 'value="Restaurant website"' in form_page.text

    response = client.post(
        "/projects/1/edit", data=project_form(name="Cafe website", status="Completed"), follow_redirects=False
    )
    assert response.status_code == 303
    db.expunge_all()
    project = db.get(Project, 1)
    assert project.name == "Cafe website"
    assert project.status == ProjectStatus.COMPLETED


def test_delete_project_removes_tasks_but_keeps_notes(client, db):
    project = project_service.create_project(db, {"name": "Shop", "category": ProjectCategory.E_COMMERCE})
    task_service.create_task(db, {"title": "Pick theme", "project_id": project.id})
    note = note_service.create_note(db, {"title": "Payment ideas", "project_id": project.id})

    response = client.post(f"/projects/{project.id}/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/projects?msg=project_deleted"
    db.expunge_all()
    assert db.query(Project).count() == 0
    assert db.query(Task).count() == 0
    kept = db.get(Note, note.id)
    assert kept is not None and kept.project_id is None


def test_list_filters_by_status_and_search(client, db):
    project_service.create_project(db, {"name": "Alpha bot", "status": ProjectStatus.IN_PROGRESS})
    project_service.create_project(db, {"name": "Beta site", "status": ProjectStatus.PLANNING})

    by_status = client.get("/projects", params={"status": "In Progress"})
    assert "Alpha bot" in by_status.text and "Beta site" not in by_status.text

    by_search = client.get("/projects", params={"q": "beta"})
    assert "Beta site" in by_search.text and "Alpha bot" not in by_search.text

    # Unknown filter values are ignored rather than causing an error.
    assert client.get("/projects", params={"status": "nonsense"}).status_code == 200


def test_project_detail_shows_tasks_and_notes(client, db):
    project = project_service.create_project(db, {"name": "Voice agent"})
    task_service.create_task(db, {"title": "Test Azerbaijani STT", "project_id": project.id})
    note_service.create_note(db, {"title": "Vendor comparison", "project_id": project.id})

    page = client.get(f"/projects/{project.id}")
    assert "Test Azerbaijani STT" in page.text
    assert "Vendor comparison" in page.text


def test_unknown_project_returns_404_page(client):
    for url in ("/projects/999", "/projects/999/edit"):
        response = client.get(url)
        assert response.status_code == 404
        assert "We couldn" in response.text
    assert client.post("/projects/999/delete").status_code == 404
