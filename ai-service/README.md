# AI Service — StudySage

Parsing, chunking, embeddings, vector search, and the RAG pipeline. Also the
quiz/flashcard/summary/planner generators.

## Setup
```bash
cd ai-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in GEMINI_API_KEY etc.
uvicorn main:app --reload --port 8001
```

## Owns
- `parser/` — PDF/DOCX/PPTX parsing, OCR
- `embeddings/` — chunking + embedding generation
- `rag/` — retrieval, re-ranking, context building, citation engine
- `quiz/` — quiz + flashcard generation
- `planner/` — study planner logic

See root `README.md` for the full picture and `/docs` for architecture.
