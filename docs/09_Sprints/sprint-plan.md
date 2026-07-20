# Sprint Plan — StudySage

Mapped to the 5 development phases (see root `README.md#roadmap`). Each
phase ≈ one sprint block; adjust cadence to weekly stand-ups given the team
is also managing coursework/placement prep.

## Epics
1. Foundation & Auth
2. Ingestion & Retrieval Core
3. RAG Chat Experience
4. AI Feature Expansion
5. Hardening, QA & Deployment

## Sprint 1 — Foundation & Setup (Week 1–2)
| Story | Owner | Points (rough) |
|---|---|---|
| Repo scaffold + CI skeleton | Sumit | 2 |
| Auth (JWT + Google OAuth) | Sumit | 5 |
| DB schema v1 | Sumit | 3 |
| Frontend shell (routing, layout, design tokens) | Gaurav | 3 |
| Finalize embeddings/vector DB choice + RAG spike | Saurabh | 5 |

**Definition of Ready:** story has an owner, a linked doc section, and no
open question blocking a start.
**Definition of Done:** merged to `develop` via reviewed PR, CI green.

## Sprint 2 — Ingestion & Retrieval Core (Week 3–4)
| Story | Owner | Points |
|---|---|---|
| Upload API + storage integration | Sumit | 5 |
| Parsing (PDF/DOCX/PPTX) + OCR | Saurabh | 5 |
| Chunking + embedding pipeline | Saurabh | 5 |
| Notes Manager UI | Gaurav | 5 |

## Sprint 3 — RAG Chat Experience (Week 5–7)
| Story | Owner | Points |
|---|---|---|
| RAG pipeline (retrieve→rerank→context→generate→cite) | Saurabh | 8 |
| Chat API + history persistence | Sumit | 3 |
| Chat UI (markdown, streaming, citations) | Gaurav (paired) | 8 |
| PDF Viewer (highlight/jump) | Gaurav (paired) | 5 |

## Sprint 4 — AI Feature Expansion (Week 8–9)
| Story | Owner | Points |
|---|---|---|
| Summarizer | Saurabh | 3 |
| Quiz + flashcard generators | Saurabh | 5 |
| Study planner logic | Saurabh | 5 |
| Analytics APIs | Sumit | 3 |
| Quiz UI + planner UI + settings | Gaurav | 5 |

## Sprint 5 — Hardening, QA & Deployment (Week 10–12)
| Story | Owner | Points |
|---|---|---|
| Security pass | All | 5 |
| Testing + bug fixes | All | 5 |
| CI/CD to staging/production | Sumit | 3 |
| AI evaluation + guardrails | Saurabh | 3 |
| UI polish + responsiveness | Gaurav | 3 |

## Risk Register
| Risk | Owner | Status |
|---|---|---|
| RAG pipeline complexity underestimated | Saurabh | Watching — de-risked via Sprint 1 spike |
| Gaurav blocked on Chat/PDF Viewer complexity | Gaurav + pair | Mitigated — paired work, not solo |
| LLM API rate limits during testing | Saurabh | Watching |

## Burndown Expectations
Points are rough sizing, not a formal estimation exercise — the real signal
is whether a phase's demo works end-to-end by its week-range, not whether
points burned down linearly.
