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
