"""Quiz generation endpoint — proxies to the AI Service's /quiz. Owner: Sumit.

No persistence yet (no quizzes/quiz_attempts tables) — returns the
generated questions directly; scoring/attempt-history is a follow-up once
those tables exist.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import User
from services.ai_client import generate_quiz
from services.ownership import get_owned_document

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    document_id: uuid.UUID
    question_count: int = Field(default=5, ge=1, le=20)
    types: list[str] = ["mcq", "true_false", "fill_blank"]


@router.post("/generate")
def generate_quiz_endpoint(
    body: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, body.document_id, current_user)
    if document.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document isn't processed yet")

    result = generate_quiz(str(document.subject_id), str(document.id), body.question_count, body.types)
    if result is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service unavailable")
    return result