# StudySage AI Service

FastAPI microservice handling document parsing, embeddings, RAG chat, and
AI-generated study content (summaries, quizzes, flashcards, study plans).

Owner: Saurabh

## Stack

- **FastAPI** — HTTP layer
- **PyMuPDF / python-docx / python-pptx** — document parsing (PDF, DOCX, PPTX)
- **sentence-transformers (all-MiniLM-L6-v2)** — embeddings
- **ChromaDB** — vector storage (one collection per subject)
- **Gemini 2.5 Flash** — generation (chat answers, summaries, quizzes, flashcards, plans)

## Local Setup

```powershell
cd ai-service
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
# source venv/bin/activate         # Mac/Linux
pip install -r requirements.txt
```

Copy the env template at the project root and fill in your key:
```powershell
cp ../.env.example ../.env
```
GEMINI_API_KEY=your-key-here # https://aistudio.google.com/apikey
VECTOR_DB_PATH=./chroma_db

**OCR support** (for scanned PDFs, not yet wired into `parser/`) needs the
Tesseract binary installed system-wide separately from pip — see the
Tesseract project docs for your OS if/when this is added.

## Running

```powershell
uvicorn main:app --reload --port 8001
```
Health check: `GET http://localhost:8001/health` → `{"status": "ok", "service": "studysage-ai"}`

## Endpoints

All endpoints are `POST` with a JSON body, and return JSON. Validation
errors return `422`; application errors (missing config, bad model output)
return `400` or `500` with a `detail` message.

### `POST /query` — RAG chat

Ask a question grounded in a subject's uploaded documents, with citations.

**Request:**
```json
{ "query": "What does the mitochondria do?", "subject_id": "subj_123" }
```
**Response:**
```json
{
  "answer": "The mitochondria generates ATP through cellular respiration.",
  "citations": [
    { "document_id": "doc_456", "page": 3, "snippet": "The mitochondria is the powerhouse..." }
  ],
  "flagged_chunks": []
}
```
`flagged_chunks` lists indices of retrieved chunks matching known
prompt-injection patterns — logged for review, not blocking the response.

### `POST /summarize` — Document summary

**Request:**
```json
{ "subject_id": "subj_123", "document_id": "doc_456", "length": "short" }
```
`length`: `"short"` | `"detailed"` | `"chapter-wise"` (default: `"short"`)

**Response:**
```json
{ "summary": "...", "length": "short", "chunk_count": 12 }
```

### `POST /quiz` — Quiz generator

**Request:**
```json
{
  "subject_id": "subj_123",
  "document_id": "doc_456",
  "question_count": 5,
  "types": ["mcq", "true_false", "fill_blank"]
}
```
`question_count`: 1–20 (default: 5). `types`: any subset of `mcq`,
`true_false`, `fill_blank` (default: all three).

**Response:**
```json
{
  "questions": [
    {"type": "mcq", "question": "...", "options": ["A", "B", "C", "D"], "answer": "B", "difficulty": "easy"},
    {"type": "true_false", "question": "...", "answer": "true", "difficulty": "medium"}
  ],
  "question_count": 2
}
```

### `POST /flashcards` — Flashcard generator

**Request:**
```json
{ "subject_id": "subj_123", "document_id": "doc_456", "card_count": 10, "difficulty": "mixed" }
```
`card_count`: 1–30 (default: 10). `difficulty`: `"easy"` | `"medium"` |
`"hard"` | `"mixed"` (default: `"mixed"`).

**Response:**
```json
{
  "flashcards": [{"question": "...", "answer": "...", "difficulty": "easy"}],
  "card_count": 1
}
```

### `POST /planner` — Study planner

Does not use document retrieval — pure scheduling based on subject/deadline input.

**Request:**
```json
{
  "subjects": [{"name": "Math", "priority": 1}, {"name": "History", "priority": 3}],
  "deadline": "2026-08-15",
  "hours_per_day": 3,
  "start_date": "2026-08-01"
}
```
`subjects[].priority`: 1 (highest) to 5 (lowest). `start_date`: optional,
defaults to today. `hours_per_day`: 0–16.

**Response:**
```json
{
  "plan": [
    {"day": 1, "date": "2026-08-01", "sessions": [{"subject": "Math", "hours": 2, "focus": "new material"}]}
  ],
  "days_available": 14
}
```

## Testing

```powershell
pytest -v
```

All tests mock Gemini API calls (`unittest.mock.patch`) — no real API key
or network access needed to run the suite, and no cost incurred. This
also means CI doesn't depend on live API availability.

`ruff check .` runs the linter; both `ruff` and `pytest` are required
checks in CI (see `.github/workflows/ai-ci.yml`).

## Evaluation (quality tracking, not a unit test)

```powershell
python eval/run_eval.py
```

Runs ~12 fixed questions against a live Gemini call to catch answer-quality
regressions. **Not run in CI** — makes real API calls (costs quota, takes
~3 minutes paced to respect free-tier rate limits) and needs human judgment
on borderline results. See `eval/README.md` for when to run this.

**Free tier limits to be aware of:** 5 requests/minute, 20 requests/day for
`gemini-2.5-flash`. The eval script paces itself for the per-minute limit;
the daily limit means you may only get one full eval run per day per API key.

## Project Structure
ai-service/
├── main.py # FastAPI app, all routes, request validation
├── parser/ # PDF/DOCX/PPTX -> [{"page": int, "text": str}, ...]
├── embeddings/ # chunking + Chroma storage/retrieval
├── rag/ # retrieve -> generate -> cite pipeline
├── summarizer/ # document summarization
├── quiz/ # quiz generation (MCQ/TF/fill-blank)
├── flashcards/ # flashcard generation
├── planner/ # study plan generation
├── eval/ # manual quality-tracking tool (not CI)
├── tests/ # pytest suite, all Gemini calls mocked
└── spike/ # Sprint 1 exploratory script, not production code

## Integration Notes for Backend (Sumit)

- All endpoints expect the backend to have already resolved `subject_id`/
  `document_id` — this service has no concept of users/auth, that's the
  backend's job.
- Documents must be ingested (parsed, chunked, embedded) before `/query`,
  `/summarize`, `/quiz`, or `/flashcards` will return meaningful results.
  There's currently no dedicated `/ingest` endpoint — flag if the backend
  needs one added, or if ingestion should happen via a different flow.
- `/planner` is the only endpoint with no document dependency.

