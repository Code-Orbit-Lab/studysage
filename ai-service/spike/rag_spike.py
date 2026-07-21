"""
Sprint 1 spike — proves the full RAG path on ONE sample PDF.
Throwaway/exploratory code, not part of the real parser/embeddings/rag modules.
Run from ai-service/ with: python spike/rag_spike.py
"""
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

# --- Load env vars from the project root .env ---
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")

if not GEMINI_API_KEY:
    sys.exit("GEMINI_API_KEY missing — check your .env file at the project root.")

genai.configure(api_key=GEMINI_API_KEY)

SAMPLE_PDF = Path(__file__).parent / "sample.pdf"
CHUNK_SIZE = 500      # word count, approximating tokens for the spike
CHUNK_OVERLAP = 50


def parse_pdf(path: Path) -> list[dict]:
    """Extract text per page. Returns [{"page": int, "text": str}, ...]"""
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append({"page": i, "text": text})
    doc.close()
    return pages


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Naive word-based chunker with overlap, keeps page number per chunk."""
    chunks = []
    for p in pages:
        words = p["text"].split()
        start = 0
        while start < len(words):
            end = start + CHUNK_SIZE
            chunks.append({"text": " ".join(words[start:end]), "page": p["page"]})
            start = end - CHUNK_OVERLAP
    return chunks


def embed_and_store(chunks: list[dict]):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_or_create_collection("spike_test")

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts).tolist()
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"page": c["page"]} for c in chunks]

    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return model, collection


def retrieve(model, collection, query: str, k: int = 3):
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)
    return [
        {"text": doc, "page": meta["page"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]


def ask_gemini(query: str, context_chunks: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[Chunk {i} | page {c['page']}]\n{c['text']}" for i, c in enumerate(context_chunks)
    )
    prompt = f"""Answer ONLY using the context below. If the context doesn't cover
the question, say so explicitly. Cite the chunk number(s) you used.

Context:
{context_block}

Question: {query}
"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    if not SAMPLE_PDF.exists():
        sys.exit(f"Put a sample PDF at {SAMPLE_PDF} first.")

    print("Parsing PDF...")
    pages = parse_pdf(SAMPLE_PDF)
    print(f"  {len(pages)} pages with text")

    print("Chunking...")
    chunks = chunk_pages(pages)
    print(f"  {len(chunks)} chunks")

    print("Embedding + storing in Chroma...")
    model, collection = embed_and_store(chunks)

    query = "What is this document about?"   # swap for a real question about your PDF
    print(f"\nQuerying: {query}")
    top_chunks = retrieve(model, collection, query)
    for c in top_chunks:
        print(f"  - retrieved from page {c['page']}")

    print("\nAsking Gemini...")
    answer = ask_gemini(query, top_chunks)
    print("\n--- ANSWER ---")
    print(answer)