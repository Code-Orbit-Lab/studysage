# ADR 0003 — Three-Tier Architecture Aligned to Team Ownership

**Status:** Accepted
**Date:** 2026-07-20

## Context
A 3-person student team needs to build and ship in parallel without
constantly blocking each other, while keeping the system simple enough to
actually finish in ~12 weeks.

## Decision
Split the system into three services with a clear API contract between
them — `frontend/` (Next.js), `backend/` (FastAPI), `ai-service/` (RAG
pipeline) — and assign one owner per service: Gaurav, Sumit, Saurabh
respectively. See [Team Responsibilities](../../README.md#team--ownership).

## Consequences
**Positive**
- Each person can develop and test their service against a documented API
  contract without waiting on the others' code to be finished — only
  integration points need coordination.
- CODEOWNERS + path-filtered CI naturally follow the same split (see
  `.github/CODEOWNERS`, `.github/workflows/`).

**Trade-offs accepted**
- Three services means three things to run locally and three deploy
  targets, more operational overhead than a single monolith — judged
  acceptable given the team-alignment benefit outweighs it at this scale.
- Cross-service changes (e.g. a new field needed by both backend and
  ai-service) need a bit more coordination than a monolith would — mitigate
  by keeping the [API Spec](../04_API/api-spec.md) as the source of truth,
  updated in the same PR as the change.
