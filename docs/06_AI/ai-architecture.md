# AI Architecture — StudySage

Owner: Saurabh. Lives in `ai-service/`.

## Document Parsing Pipeline
| Input | Library |
|---|---|
| PDF | PyMuPDF (primary), pdfplumber (tables/layout) |
| DOCX | python-docx |
| PPTX | python-pptx |
| Images / scanned pages | pytesseract (OCR) |

Output of this stage is always plain text + page/slide number metadata,
regardless of source format — everything downstream is format-agnostic.

## Chunking Strategy
Recursive character/token splitter (~500 tokens, ~50-token overlap) as the
default. Keep page number attached to every chunk — this is what makes
citations possible later. Revisit with semantic chunking if retrieval
quality on long documents needs improvement.

## Embeddings
Sentence-Transformers (open-source, free, runs locally — no per-call cost)
as the default. Re-evaluate against Gemini embeddings if retrieval quality
needs a boost and the API cost is acceptable.

## Vector Database
ChromaDB for local/dev (zero setup, embedded). Qdrant is the fallback if
scale or filtering needs outgrow Chroma. One collection per subject (or a
single collection filtered by `subject_id` metadata) — decide based on
expected subject count per user; start with metadata filtering, it's
simpler to operate.

## RAG Pipeline
```
User query
   │
Embed query
   │
Retrieve top-k chunks (vector similarity, filtered by subject_id)
   │
Re-rank (cross-encoder or simple recency/relevance heuristic to start)
   │
Build context window (chunks + their page metadata)
   │
Call LLM (Gemini 2.5 Flash) with a grounded-answer prompt
   │
Parse answer + map cited chunks back to (document, page)
   │
Return answer + citations
```

## Prompt Engineering Notes
- System prompt instructs the model to answer **only** from the provided
  context and to explicitly say when the context doesn't cover the
  question — this is the main hallucination guard, backed by NFR-1 in the
  [PRD](../01_PRD/prd.md#non-functional-requirements).
- Every context chunk is passed with an ID; the model is asked to tag which
  chunk ID(s) it used, which is what gets mapped to citations.

## Quiz / Flashcard / Summarizer / Planner
All reuse the same retrieval step as chat, but swap the generation prompt:
- **Summarizer** — retrieve broadly across the whole document, prompt for
  short/detailed/chapter-wise output.
- **Quiz/Flashcards** — retrieve broadly, prompt for structured JSON output
  (question/options/answer/difficulty), validated before returning to the
  Backend.
- **Planner** — no document retrieval; takes subjects + deadline + hours as
  structured input and prompts for a day-by-day JSON schedule.

## Hallucination Prevention
1. Context-only answering (see prompt notes above).
2. Citation requirement — if the model can't cite a chunk, the Backend
   treats the answer as low-confidence and flags it in the UI.
3. Manual spot-checking during Phase 5 hardening against a small labeled
   test set of question/expected-citation pairs.

## Evaluation
Lightweight, not academic: a test set of ~20 question/document pairs where
the correct page is known ahead of time, checked after any change to
chunking, embeddings, or the retrieval prompt.
