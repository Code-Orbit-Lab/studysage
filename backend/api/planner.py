"""Study planner endpoint — proxies to the AI Service's /planner. Owner: Sumit.

Saurabh's planner takes subject *names*, not IDs. This endpoint accepts
our subject_ids instead (so ownership is enforced the normal way) and
resolves them to names before calling the AI service — the ID<->name
translation lives here so every other layer stays ID-based.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import User
from services.ai_client import generate_plan
from services.ownership import get_owned_subject

router = APIRouter()


class PlannerSubject(BaseModel):
    subject_id: uuid.UUID
    priority: int = Field(ge=1, le=5)


class PlannerGenerateRequest(BaseModel):
    subjects: list[PlannerSubject] = Field(min_length=1, max_length=20)
    deadline: str
    hours_per_day: float = Field(gt=0, le=16)
    start_date: str | None = None


@router.post("/generate")
def generate_plan_endpoint(
    body: PlannerGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resolved = [
        {"name": get_owned_subject(db, s.subject_id, current_user).name, "priority": s.priority}
        for s in body.subjects
    ]

    result = generate_plan(resolved, body.deadline, body.hours_per_day, body.start_date)
    if result is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service unavailable")
    return result