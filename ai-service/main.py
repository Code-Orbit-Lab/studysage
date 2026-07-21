"""
StudySage AI Service — parsing, embeddings, RAG pipeline.
Owner: Saurabh

Run locally:
    uvicorn main:app --reload --port 8001
"""
from fastapi import FastAPI

app = FastAPI(title="StudySage AI Service", version="0.1.0")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "studysage-ai"}


# TODO(saurabh): wire up as each piece is built
# from rag.pipeline import router as rag_router
# app.include_router(rag_router, prefix="/rag", tags=["rag"])
from fastapi import HTTPException
from pydantic import BaseModel

from rag import answer_query


class QueryRequest(BaseModel):
    query: str
    subject_id: str


@app.post("/query")
def query_endpoint(request: QueryRequest):
    try:
        return answer_query(request.query, request.subject_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
