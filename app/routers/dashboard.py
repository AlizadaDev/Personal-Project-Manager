from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import projects as project_service
from app.services.dashboard import get_dashboard
from app.templating import render

router = APIRouter(tags=["dashboard"])


@router.get("/")
def dashboard(request: Request, db: Annotated[Session, Depends(get_db)]):
    context = {"d": get_dashboard(db), "progress": project_service.task_progress(db)}
    return render(request, "dashboard.html", context)
