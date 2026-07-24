"""Flashcard generation endpoint — proxies to the AI Service's /flashcards.
Owner: Sumit.

No persistence yet (no flashcards table) — returns the generated cards
directly; saving them for spaced review is a follow-up.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import Flashcard, User
from services.ai_client import generate_flashcards
from services.ownership import get_owned_document
from services.rate_limit import LLM_ENDPOINT_LIMIT, limiter

router = APIRouter()


class FlashcardGenerateRequest(BaseModel):
    document_id: uuid.UUID
    card_count: int = Field(default=10, ge=1, le=30)
    difficulty: str = "mixed"


@router.post("/generate")
@limiter.limit(LLM_ENDPOINT_LIMIT)
def generate_flashcards_endpoint(
    request: Request,
    body: FlashcardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, body.document_id, current_user)
    if document.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Document isn't processed yet"
        )

    result = generate_flashcards(
        str(document.subject_id), str(document.id), body.card_count, body.difficulty
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable",
        )

    for card in result["flashcards"]:
        db.add(
            Flashcard(
                subject_id=document.subject_id,
                question=card["question"],
                answer=card["answer"],
                difficulty=card.get("difficulty", "mixed"),
            )
        )

    db.commit()

    return result
