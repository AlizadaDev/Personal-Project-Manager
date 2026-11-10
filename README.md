# Personal Project Manager

A simple local web app for managing business ideas, projects, tasks and notes.
Built with FastAPI, SQLite, SQLAlchemy 2.0 and Jinja2. Single user, runs only on your computer.

## Run

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. The database is created automatically at `data/app.db`.
To back up your data, copy that file.

## Test

```powershell
pip install -r requirements-dev.txt
pytest
```

Tests use a temporary database and never touch `data/app.db`.

## Structure

| Path | What it does |
|---|---|
| `app/main.py` | Creates the app, mounts static files, registers routers, 404 page |
| `app/models.py` | Database tables: `Project`, `Task`, `Note` |
| `app/enums.py` | Statuses, categories and priorities |
| `app/validation.py` | Turns form input into clean data + error messages |
| `app/services/` | All database logic (no HTTP/HTML) |
| `app/routers/` | Pages and form handlers (no SQL) |
| `app/templates/` | Jinja2 pages; shared UI pieces live in `partials/_macros.html` |
| `app/static/` | `style.css` (design system, light/dark) and `app.js` (small enhancements) |

## Behaviour notes

- Deleting a project also deletes its tasks. Its notes are kept and become unlinked.
- "Active projects" means the status is *In Progress*. "Pending tasks" means any task that isn't *Done*.
- The app has no login, so don't expose it beyond `127.0.0.1`.
- Tables are created with `create_all()`. If you later change a model on a database that already holds data, add a migration tool (Alembic) or recreate the table.
