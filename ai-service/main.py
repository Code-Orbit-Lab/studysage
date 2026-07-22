"""
StudySage AI Service — parsing, embeddings, RAG pipeline.
Owner: Saurabh

Run locally:
    uvicorn main:app --reload --port 8001
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag import answer_query
from summarizer import summarize_document
from quiz import generate_quiz
from flashcards import generate_flashcards


app = FastAPI(title="StudySage AI Service", version="0.1.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "studysage-ai"}


# TODO(saurabh): wire up as each piece is built
class QueryRequest(BaseModel):
    query: str
    subject_id: str


@app.post("/query")
def query_endpoint(request: QueryRequest):
    try:
        return answer_query(request.query, request.subject_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class SummaryRequest(BaseModel):
    subject_id: str
    document_id: str
    length: str = "short"


@app.post("/summarize")
def summarize_endpoint(request: SummaryRequest):
    try:
        return summarize_document(request.subject_id, request.document_id, request.length)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))



class QuizRequest(BaseModel):
    subject_id: str
    document_id: str
    question_count: int = 5
    types: list[str] = ["mcq", "true_false", "fill_blank"]


@app.post("/quiz")
def quiz_endpoint(request: QuizRequest):
    try:
        return generate_quiz(request.subject_id, request.document_id, request.question_count, request.types)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class FlashcardRequest(BaseModel):
    subject_id: str
    document_id: str
    card_count: int = 10
    difficulty: str = "mixed"


@app.post("/flashcards")
def flashcards_endpoint(request: FlashcardRequest):
    try:
        return generate_flashcards(request.subject_id, request.document_id, request.card_count, request.difficulty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))