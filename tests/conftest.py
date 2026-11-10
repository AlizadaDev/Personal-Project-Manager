"""Test setup: point the app at a throwaway SQLite file *before* the app is imported,
so the real data/app.db is never touched."""

import os
import tempfile
from pathlib import Path

_TMP_DIR = Path(tempfile.mkdtemp(prefix="ppm-tests-"))
os.environ["PPM_DATABASE_URL"] = f"sqlite:///{(_TMP_DIR / 'test.db').as_posix()}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402,F401
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def project_form(**overrides) -> dict[str, str]:
    data = {
        "name": "Restaurant website",
        "description": "Landing page + menu",
        "category": "Web Development",
        "status": "In Progress",
        "start_date": "2026-11-01",
        "deadline": "2026-12-01",
    }
    data.update(overrides)
    return data


def task_form(**overrides) -> dict[str, str]:
    data = {
        "title": "Design homepage",
        "description": "",
        "project_id": "",
        "priority": "High",
        "status": "To Do",
        "due_date": "",
    }
    data.update(overrides)
    return data
