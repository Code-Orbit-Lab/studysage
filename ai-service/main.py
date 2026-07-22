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