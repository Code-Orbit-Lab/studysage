# Project Charter — StudySage (AI Study Assistant)

## Vision
Give students one place to upload everything they're studying from and get
answers, revision material, and a study plan back — grounded in their own
material, cited to the source page, not a generic AI guess.

## Problem Statement
- Study material is scattered across drives, WhatsApp, PDFs, and printed notes.
- Revising before an exam means re-reading everything; there's no fast way to
  query "what do my notes say about X".
- Making quizzes, flashcards, and summaries by hand is slow and gets skipped
  under deadline pressure.
- General-purpose AI chatbots don't persist a student's material, don't cite
  the source page, and hallucinate on niche/lecture-specific topics.
- There's no structured way to turn "10 subjects, 3 weeks left" into an
  actual day-by-day plan.

## Objective
Ship a working RAG-based study platform — upload, chat with citations,
summarize, quiz, flashcards, planner, progress tracking — over a 12-week,
5-phase build.

## Team
| Member | Role | Owns |
|---|---|---|
| Sumit Gupta | Backend & Infra / Integration Lead | `backend/` |
| Saurabh | AI/ML Lead | `ai-service/` |
| Gaurav | Frontend | `frontend/` |

## Scope
Upload (PDF/DOCX/PPTX/images) → RAG chat with citations → summarizer → quiz
generator → flashcard generator → study planner → progress analytics → auth
(JWT + Google OAuth).

## Out of Scope (v1)
- Mobile app (web-responsive only for now)
- Voice-based Q&A
- Handwritten-notes recognition
- Multi-language support
- Collaborative study groups

## Success Metrics
- All three services (frontend/backend/ai-service) deployed and talking to
  each other by end of Phase 3.
- RAG answers cite a real source page for a representative test set of
  uploaded documents.
- End-to-end demo (upload → chat → quiz → plan) working by end of Phase 5.

## Constraints & Assumptions
- Free/open-source-first stack — no team budget, only real running cost is
  LLM API calls (Gemini free tier).
- 3-person team, ~12 weeks, alongside coursework/placement prep — plan
  workload accordingly (see [Sprint Plan](../09_Sprints/sprint-plan.md)).
- Gaurav is newer to the stack — default workload favors well-scoped,
  lower-complexity screens (see [Team Responsibilities](../../README.md#team--ownership)).

## Risks
| Risk | Mitigation |
|---|---|
| RAG pipeline is the hardest, most novel piece | Owned solo by Saurabh, de-risked with a Phase 1 spike before the rest of the team builds on top of it |
| LLM free-tier rate limits during demo | Cache/log responses during dev, avoid hammering the API in tests |
| Team members blocked on each other | Layered architecture with clear API contracts (see [System Design](../03_System_Design/system-design.md)) |

## Full Snapshot
See [`docs/Architecture.pdf`](../Architecture.pdf) for the point-in-time
architecture, phase plan, and engineering standards document shared with the
team on 20 July 2026.
