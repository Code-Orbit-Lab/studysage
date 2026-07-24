"""Chat endpoint — proxies to the AI Service's RAG /query, and persists
the turn to `chat_messages`. Owner: Sumit.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import ChatMessage, User
from services.ai_client import query_ai_service
from services.ownership import get_owned_subject, require_ready_document_in_subject
from services.rate_limit import LLM_ENDPOINT_LIMIT, limiter

router = APIRouter()


class ChatQueryRequest(BaseModel):
    subject_id: uuid.UUID
    message: str = Field(min_length=1, max_length=2000)


@router.post("/query")
@limiter.limit(LLM_ENDPOINT_LIMIT)
def chat_query(
    request: Request,
    body: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_subject(db, body.subject_id, current_user)
    require_ready_document_in_subject(db, body.subject_id)

    result = query_ai_service(body.message, str(body.subject_id))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable",
        )

    # Persist the full turn only once we actually have an answer -- a
    # failed AI call leaves nothing behind rather than a question with no
    # reply sitting in the history.
    db.add(ChatMessage(subject_id=body.subject_id, role="user", content=body.message))
    db.add(
        ChatMessage(
            subject_id=body.subject_id,
            role="assistant",
            content=result.get("answer", ""),
            citations=result.get("citations"),
        )
    )
    db.commit()

    return result


@router.get("/history")
def chat_history(
    subject_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_subject(db, subject_id, current_user)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.subject_id == subject_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": m.citations,
            "created_at": m.created_at,
        }
        for m in messages
    ]
