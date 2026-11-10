"""Application settings. Kept as plain constants: this is a single-user local app."""

import os
from pathlib import Path

APP_NAME = "Project Manager"

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"

# Override with PPM_DATABASE_URL (the test suite does this to use a temporary database).
DATABASE_URL = os.getenv(
    "PPM_DATABASE_URL", f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
)
