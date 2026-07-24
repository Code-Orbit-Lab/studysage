"""Notes/upload endpoints — the backend<->AI-service integration point.
Owner: Sumit."""
import os
import uuid

"check for error"

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import SessionLocal, get_db
from models import Document, User
from services.ai_client import summarize_document, trigger_processing
from services.file_validation import detect_file_type
from services.ownership import get_owned_document, get_owned_subject
from services.storage import delete_file, save_file

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20")) * 1024 * 1024


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    page_count: int | None

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    document_id: uuid.UUID
    status: str


class SummarizeRequest(BaseModel):
    length: str = "short"  # "short" | "detailed" | "chapter-wise"


def _process_in_background(document_id: str, subject_id: str, storage_path: str, file_type: str) -> None:
    """Runs after the response is sent — owns its own DB session since the
    request-scoped one is already closed by then."""
    db = SessionLocal()
    try:
        ok = trigger_processing(document_id, subject_id, storage_path, file_type)
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if doc:
            doc.status = "ready" if ok else "failed"
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_note(
    background_tasks: BackgroundTasks,
    subject_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_subject(db, subject_id, current_user)

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    file_type = detect_file_type(content)
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported or unrecognized file type",
        )

    storage_path = save_file(str(current_user.id), str(subject_id), file.filename, content)

    document = Document(
        subject_id=subject_id,
        filename=file.filename,
        file_type=file_type,
        storage_path=storage_path,
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(
        _process_in_background, str(document.id), str(subject_id), storage_path, file_type
    )

    return UploadResponse(document_id=document.id, status="processing")


@router.get("", response_model=list[DocumentOut])
def list_notes(
    subject_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_subject(db, subject_id, current_user)
    return db.query(Document).filter(Document.subject_id == subject_id).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_note(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_document(db, document_id, current_user)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, document_id, current_user)
    delete_file(document.storage_path)
    db.delete(document)
    db.commit()


@router.post("/{document_id}/summarize")
def summarize_note(
    document_id: uuid.UUID,
    body: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, document_id, current_user)
    if document.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document isn't processed yet")

    result = summarize_document(str(document.subject_id), str(document.id), body.length)
    if result is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service unavailable")
    return result