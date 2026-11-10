from app.models import Note
from app.services import notes as note_service
from app.services import projects as project_service


def test_create_note_linked_to_project(client, db):
    project = project_service.create_project(db, {"name": "AI content"})

    response = client.post(
        "/notes",
        data={"title": "Post ideas", "content": "1. Reels\n2. Carousels", "project_id": str(project.id)},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/notes/1?msg=note_created"
    page = client.get("/notes/1")
    assert "Post ideas" in page.text and "AI content" in page.text
    assert "Post ideas" in client.get(f"/projects/{project.id}").text


def test_note_title_is_required(client, db):
    response = client.post("/notes", data={"title": "", "content": "x"})
    assert response.status_code == 422
    assert db.query(Note).count() == 0


def test_edit_and_delete_note(client, db):
    note = note_service.create_note(db, {"title": "Draft", "content": "old"})

    assert "old" in client.get(f"/notes/{note.id}/edit").text
    response = client.post(f"/notes/{note.id}/edit", data={"title": "Final", "content": "new"}, follow_redirects=False)
    assert response.headers["location"] == f"/notes/{note.id}?msg=note_updated"
    db.expunge_all()
    assert db.get(Note, note.id).title == "Final"

    response = client.post(f"/notes/{note.id}/delete", follow_redirects=False)
    assert response.headers["location"] == "/notes?msg=note_deleted"
    db.expunge_all()
    assert db.get(Note, note.id) is None


def test_search_and_project_filter(client, db):
    project = project_service.create_project(db, {"name": "Voice AI"})
    note_service.create_note(db, {"title": "Pricing", "content": "monthly retainer"})
    note_service.create_note(db, {"title": "Vendors", "content": "Vapi vs Retell", "project_id": project.id})

    assert "Vendors" not in client.get("/notes", params={"q": "retainer"}).text
    assert "Pricing" in client.get("/notes", params={"q": "retainer"}).text

    linked = client.get("/notes", params={"project": str(project.id)}).text
    assert "Vendors" in linked and "Pricing" not in linked

    unlinked = client.get("/notes", params={"project": "none"}).text
    assert "Pricing" in unlinked and "Vendors" not in unlinked


def test_unknown_note_returns_404(client):
    assert client.get("/notes/123").status_code == 404
