"""Chat endpoint — proxies to the AI Service's RAG /query. Owner: Sumit.

No persistence yet (no chat_messages table) — returns the answer directly;
history is a follow-up once that table exists.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import User
from services.ai_client import query_ai_service
from services.ownership import get_owned_subject, require_ready_document_in_subject

router = APIRouter()


class ChatQueryRequest(BaseModel):
    subject_id: uuid.UUID
    message: str = Field(min_length=1, max_length=2000)


@router.post("/query")
def chat_query(
    body: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_subject(db, body.subject_id, current_user)
    require_ready_document_in_subject(db, body.subject_id)

    result = query_ai_service(body.message, str(body.subject_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service unavailable")
    return result