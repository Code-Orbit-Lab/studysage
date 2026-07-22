"""
StudySage AI Service — parsing, embeddings, RAG pipeline.
Owner: Saurabh

Run locally:
    uvicorn main:app --reload --port 8001
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from rag import answer_query
from summarizer import summarize_document
from quiz import generate_quiz
from flashcards import generate_flashcards
from planner import generate_study_plan

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