"""Embedding generation + Chroma storage. Owner: Saurabh

One Chroma collection per subject (subject_id) — chosen over one giant
collection with metadata filtering per docs/06_AI, since subject-level
isolation is simpler to reason about at our expected scale (a student's
handful of subjects, not thousands of tenants).
"""
import os
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Cached — loading the model is expensive, only do it once per process."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=VECTOR_DB_PATH)


def get_collection(subject_id: str):
    client = get_chroma_client()
    return client.get_or_create_collection(f"subject_{subject_id}")


def embed_and_store(chunks: list[dict], subject_id: str, document_id: str) -> int:
    """
    chunks: [{"text": str, "page": int}, ...] — output of chunker.chunk_pages()
    Returns the number of chunks stored.
    """
    if not chunks:
        return 0

    model = get_embedding_model()
    collection = get_collection(subject_id)

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts).tolist()
    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"page": c["page"], "document_id": document_id} for c in chunks]

    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return len(chunks)


def retrieve(query: str, subject_id: str, k: int = 5) -> list[dict]:
    """Returns [{"text": str, "page": int, "document_id": str}, ...] top-k matches."""
    model = get_embedding_model()
    collection = get_collection(subject_id)

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)

    if not results["documents"] or not results["documents"][0]:
        return []

    return [
        {"text": doc, "page": meta["page"], "document_id": meta["document_id"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]