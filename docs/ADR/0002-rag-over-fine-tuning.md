# ADR 0002 — Retrieval-Augmented Generation, Not Fine-Tuning

**Status:** Accepted
**Date:** 2026-07-20

## Context
StudySage needs to answer questions grounded in each student's own,
constantly-changing set of uploaded documents. We need to choose between
fine-tuning a model per user/corpus versus retrieval-augmented generation
(RAG) against a general-purpose LLM.

## Decision
Use RAG: embed and index each user's documents in a vector store, retrieve
relevant chunks at query time, and pass them as context to a general-
purpose LLM (Gemini 2.5 Flash) rather than fine-tuning a model.

## Consequences
**Positive**
- New uploads are searchable within minutes (embed + index), no retraining
  cycle.
- Answers can be cited back to a specific chunk/page, directly satisfying
  NFR-1 (no un-cited claims) — much harder to guarantee with a fine-tuned
  model's generated text.
- No per-user model to host, version, or pay to train — fits the
  free/open-source-first constraint from the [Project Charter](../00_Project_Charter/charter.md).

**Trade-offs accepted**
- Answer quality depends on retrieval quality — a bad chunking/embedding
  choice hurts more than it would with a fine-tuned model that "just
  knows" the material. Mitigated by the evaluation approach in
  [AI Architecture](../06_AI/ai-architecture.md#evaluation).
- Context-window limits cap how much material can be considered per query
  — acceptable at student-notes scale, would need revisiting for
  book-length corpora.
