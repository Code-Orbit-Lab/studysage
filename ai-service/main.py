"""
StudySage AI Service — parsing, embeddings, RAG pipeline.
Owner: Saurabh

Run locally:
    uvicorn main:app --reload --port 8001
"""
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from rag import answer_query
from summarizer import summarize_document
from quiz import generate_quiz
from flashcards import generate_flashcards
from planner import generate_study_plan
from parser import parse_document
from embeddings import chunk_pages, embed_and_store
from storage import download_from_storage

app = FastAPI(title="StudySage AI Service", version="0.1.0")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "studysage-ai"}


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    subject_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("query", "subject_id")
    @classmethod
    def strip_and_check_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank or whitespace-only")
        return v


@app.post("/query")
def query_endpoint(request: QueryRequest):
    try:
        return answer_query(request.query, request.subject_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class SummaryRequest(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=100)
    document_id: str = Field(..., min_length=1, max_length=100)
    length: str = "short"

    @field_validator("subject_id", "document_id")
    @classmethod
    def strip_and_check_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank or whitespace-only")
        return v


@app.post("/summarize")
def summarize_endpoint(request: SummaryRequest):
    try:
        return summarize_document(request.subject_id, request.document_id, request.length)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class QuizRequest(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=100)
    document_id: str = Field(..., min_length=1, max_length=100)
    question_count: int = Field(default=5, ge=1, le=20)
    types: list[str] = ["mcq", "true_false", "fill_blank"]

    @field_validator("subject_id", "document_id")
    @classmethod
    def strip_and_check_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank or whitespace-only")
        return v


@app.post("/quiz")
def quiz_endpoint(request: QuizRequest):
    try:
        return generate_quiz(request.subject_id, request.document_id, request.question_count, request.types)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class FlashcardRequest(BaseModel):
    subject_id: str = Field(..., min_length=1, max_length=100)
    document_id: str = Field(..., min_length=1, max_length=100)
    card_count: int = Field(default=10, ge=1, le=30)
    difficulty: str = "mixed"

    @field_validator("subject_id", "document_id")
    @classmethod
    def strip_and_check_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank or whitespace-only")
        return v


@app.post("/flashcards")
def flashcards_endpoint(request: FlashcardRequest):
    try:
        return generate_flashcards(request.subject_id, request.document_id, request.card_count, request.difficulty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class PlannerRequest(BaseModel):
    subjects: list[dict] = Field(..., min_length=1, max_length=20)
    deadline: str
    hours_per_day: float = Field(..., gt=0, le=16)
    start_date: str | None = None


@app.post("/planner")
def planner_endpoint(request: PlannerRequest):
    try:
        return generate_study_plan(request.subjects, request.deadline, request.hours_per_day, request.start_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProcessRequest(BaseModel):
    document_id: str = Field(..., min_length=1, max_length=100)
    subject_id: str = Field(..., min_length=1, max_length=100)
    storage_path: str = Field(..., min_length=1)
    file_type: str = Field(..., min_length=1, max_length=10)


@app.post("/process")
def process_endpoint(request: ProcessRequest):
    """
    Called by the backend after a file is uploaded to Supabase Storage.
    Downloads, parses, chunks, and embeds the document. Returns 200 on
    success; the backend's ai_client.py treats any non-200 as failure and
    marks the document 'failed' rather than retrying automatically.
    """
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = download_from_storage(request.storage_path, Path(tmp_dir))
            # parse_document dispatches on file extension, so ensure the temp
            # file has the right suffix even if storage_path doesn't include one
            if not local_path.suffix:
                local_path = local_path.with_suffix(f".{request.file_type}")

            pages = parse_document(local_path)
            chunks = chunk_pages(pages)
            stored_count = embed_and_store(chunks, subject_id=request.subject_id, document_id=request.document_id)

        return {"status": "ready", "chunk_count": stored_count}

    except RuntimeError as e:
        # Includes the storage-not-configured case above
        raise HTTPException(status_code=503, detail=str(e))
    except (ValueError, NotImplementedError) as e:
        raise HTTPException(status_code=400, detail=str(e))