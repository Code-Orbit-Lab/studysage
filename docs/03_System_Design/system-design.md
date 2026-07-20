# System Design — StudySage

## High-Level Architecture
See [`docs/Architecture.pdf`](../Architecture.pdf) §2.2 for the diagram.
Three decoupled layers, one per team member:

```
Next.js Frontend  →  FastAPI Backend  →  AI Service (RAG)
                          │                    │
                    PostgreSQL          Vector DB + LLM API
                    Supabase Storage
```

## Why This Split
- Maps directly onto the 3-person team — each owns a layer with a clear API
  contract instead of stepping on each other's code.
- RAG instead of fine-tuning — cheaper, grounded in citations, updates
  instantly when a new file is uploaded (no retraining).
- Vector DB is separate from PostgreSQL because relational databases aren't
  built for approximate nearest-neighbor search over embeddings.

## Upload Flow
1. Client uploads a file to the Backend.
2. Backend stores the file in Supabase Storage, writes a metadata row in
   PostgreSQL, and calls the AI Service.
3. AI Service parses the document (OCR if scanned), chunks it, generates
   embeddings, and stores vectors in the Vector DB tagged with user/doc ID.

## Chat Flow
1. User asks a question in the Chat UI.
2. Backend forwards the query + subject context to the AI Service.
3. AI Service embeds the query, retrieves top-k chunks from the Vector DB,
   re-ranks them, builds a context window, and calls the LLM.
4. LLM answer + citations (document + page) return through the Backend,
   which logs the exchange to chat history.
5. Frontend renders the answer with clickable citations that jump to the
   page in the PDF Viewer.

## Quiz / Flashcard / Planner Flow
Same retrieval step as chat, but the AI Service uses a generation prompt
tuned for structured output (question/answer/difficulty, or a day-by-day
schedule) instead of a conversational answer. See
[AI Architecture](../06_AI/ai-architecture.md).

## Auth Flow
1. Email/password or Google OAuth via the Backend.
2. Backend issues a short-lived JWT access token (+ refresh token).
3. Frontend attaches the JWT on every API call; Backend validates it on
   each protected route.

## Deployment Topology
| Service | Where | Notes |
|---|---|---|
| Frontend | Vercel | Auto-deploys on merge to `main` |
| Backend | Render | Auto-deploys on merge to `main` |
| AI Service | Render | Separate service, own scaling |
| PostgreSQL + Storage | Supabase | Managed |
| Vector DB | ChromaDB (self-hosted alongside AI Service) or Qdrant Cloud free tier |

Full CI/CD detail: [DevOps](../08_DevOps/devops.md).
