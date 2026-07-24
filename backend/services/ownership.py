"""
Shared ownership-check helpers — every resource a user can access must be
scoped to that user, checked here so the same 404-not-403 policy applies
consistently everywhere it's needed. Owner: Sumit.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Document, Quiz, Subject, User


def get_owned_subject(db: Session, subject_id: uuid.UUID, user: User) -> Subject:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None or subject.user_id != user.id:
        # 404, not 403 — don't confirm existence of a subject the caller doesn't own
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found"
        )
    return subject


def get_owned_quiz(db: Session, quiz_id: uuid.UUID, user: User) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
        )
    get_owned_subject(
        db, quiz.subject_id, user
    )  # ownership flows through the parent subject
    return quiz


def get_owned_document(db: Session, document_id: uuid.UUID, user: User) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    get_owned_subject(
        db, document.subject_id, user
    )  # ownership flows through the parent subject
    return document


def require_ready_document_in_subject(db: Session, subject_id: uuid.UUID) -> None:
    """For subject-level operations (chat) — at least one processed
    document must exist somewhere in the subject."""
    ready = (
        db.query(Document)
        .filter(Document.subject_id == subject_id, Document.status == "ready")
        .first()
    )
    if ready is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No processed documents in this subject yet — upload and wait for processing to finish.",
        )
