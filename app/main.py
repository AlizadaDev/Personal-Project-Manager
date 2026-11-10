"""Application entry point: ``uvicorn app.main:app --reload``"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import APP_DIR, APP_NAME
from app.database import init_db
from app.routers import dashboard, notes, projects, tasks
from app.templating import render


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

for module in (dashboard, projects, tasks, notes):
    app.include_router(module.router)


@app.exception_handler(StarletteHTTPException)
async def not_found_page(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and not request.url.path.startswith("/static"):
        return render(request, "errors/404.html", status_code=404)
    return await http_exception_handler(request, exc)
