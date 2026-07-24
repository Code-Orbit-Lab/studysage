"""Study planner endpoint — proxies to the AI Service's /planner. Owner: Sumit.

Saurabh's planner takes subject *names*, not IDs. This endpoint accepts
our subject_ids instead (so ownership is enforced the normal way) and
resolves them to names before calling the AI service — the ID<->name
translation lives here so every other layer stays ID-based.
"""
import uuid
from datetime import date


from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import StudyPlan, User
from services.ai_client import generate_plan
from services.ownership import get_owned_subject
from services.rate_limit import limiter, LLM_ENDPOINT_LIMIT

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
@limiter.limit(LLM_ENDPOINT_LIMIT)
def generate_plan_endpoint(
    request: Request,
    body: PlannerGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resolved = [
        {"name": get_owned_subject(db, s.subject_id, current_user).name, "priority": s.priority}
        for s in body.subjects
    ]


    result = generate_plan(
    resolved,
    body.deadline,
    body.hours_per_day,
    body.start_date,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable",
        )

    study_plan = StudyPlan(
        user_id=current_user.id,
        deadline=date.fromisoformat(body.deadline),
        hours_per_day=body.hours_per_day,
        plan_json=result["plan"],
    )

    db.add(study_plan)
    db.commit()
    db.refresh(study_plan)

    return {
        "study_plan_id": str(study_plan.id),
        **result,
    }