# StudySage

**Chat with your own notes. Get answers cited back to the exact page.**

StudySage is an AI-powered study platform. Upload your PDFs, DOCX, PPTX, and
scanned notes, then chat with them, generate summaries/quizzes/flashcards,
and get a personalized study plan — every answer grounded in *your* material
with source citations, not a generic AI guess.

Built by **Sumit Gupta**, **Saurabh**, and **Gaurav**.

---

## Features

| Feature | What it does |
|---|---|
| Material Upload | PDF, DOCX, PPTX, images (OCR) organized by subject |
| Chat with Notes | RAG-based Q&A grounded in your uploads, with page-level citations |
| Summarizer | Short / detailed / chapter-wise summaries |
| Quiz Generator | Auto-generated MCQ, fill-in-the-blank, true/false with scoring |
| Flashcard Generator | Q&A pairs with difficulty tagging |
| Study Planner | Day-by-day plan from subjects, deadlines, and available hours |
| Progress Tracking | Analytics on study activity and quiz performance |

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js, React, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT + Google OAuth |
| AI Service | PyMuPDF, Sentence-Transformers, ChromaDB, Gemini API |
| Storage | Supabase Storage |

## Repository Structure

```text
ai-study-assistant/
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── workflows/           # per-service CI (backend/frontend/ai-service)
│   ├── CODEOWNERS
│   └── labels.md
│
├── docs/
│   ├── 00_Project_Charter/
│   ├── 01_PRD/
│   ├── 02_UX/
│   ├── 03_System_Design/
│   ├── 04_API/
│   ├── 05_Database/
│   ├── 06_AI/
│   ├── 07_Security/
│   ├── 08_DevOps/
│   ├── 09_Sprints/
│   ├── 10_Meeting_Notes/
│   ├── Architecture.pdf     # point-in-time architecture/phase-plan snapshot
│   └── ADR/                 # architecture decision records
│
├── frontend/                 # Gaurav — Next.js
├── backend/                  # Sumit — FastAPI
├── ai-service/                # Saurabh — RAG pipeline
├── infrastructure/           # deploy configs (Render/Vercel/Supabase)
├── scripts/                  # setup.sh, seed_db.py
├── tests/                    # cross-service integration tests
│
├── .env.example
├── docker-compose.yml        # local Postgres for dev
├── README.md
└── LICENSE
```

Each service folder (`backend/`, `frontend/`, `ai-service/`) has its own
`README.md` with setup steps and what it owns. `docs/` is numbered so it
reads top-to-bottom like a real engineering doc set — start at
[`docs/00_Project_Charter/charter.md`](docs/00_Project_Charter/charter.md)
if you're new to the project.

## Getting Started

1. **Clone and branch off `develop`**
   ```bash
   git clone <repo-url>
   cd ai-study-assistant
   git checkout develop
   ```
2. **Bootstrap everything** (or run steps manually — see each service's README)
   ```bash
   ./scripts/setup.sh
   ```
3. **Copy env file**
   ```bash
   cp .env.example .env
   # fill in JWT_SECRET, GEMINI_API_KEY, GOOGLE_CLIENT_ID/SECRET, SUPABASE_URL/KEY
   ```
4. **Run your service:**

| Service | Port | Run from |
|---|---|---|
| Backend | `8000` | `backend/` |
| AI Service | `8001` | `ai-service/` |
| Frontend | `3000` | `frontend/` |

## Team & Ownership

| Member | Owns | Folder |
|---|---|---|
| **Sumit** | Auth, DB schema, upload/notes/analytics APIs, integration glue, CI/CD | `backend/` |
| **Saurabh** | Parsing, embeddings, vector DB, RAG pipeline, quiz/flashcard/summary/planner generators | `ai-service/` |
| **Gaurav** | Landing, Dashboard, Notes Manager, Settings — paired on Chat UI/PDF Viewer/Quiz UI | `frontend/` |

`.github/CODEOWNERS` auto-requests the right reviewer based on which folder
a PR touches.

## Contribution Workflow

- **Branches:** `main` (protected, production) ← `develop` (protected, integration) ← `feature/*` / `fix/*`
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat(ai): add citation engine`, `fix(auth): correct token expiry`
- **PRs:** every change via PR into `develop`, 1 teammate review required, CI must pass, squash-merge
- **Issues:** use the templates in `.github/ISSUE_TEMPLATE/`, label per `.github/labels.md`

Full engineering standards: [`docs/Architecture.pdf`](docs/Architecture.pdf) §5.

## Documentation Map

| Doc | Covers |
|---|---|
| [`docs/00_Project_Charter`](docs/00_Project_Charter/charter.md) | Vision, problem, scope, success metrics |
| [`docs/01_PRD`](docs/01_PRD/prd.md) | Requirements, personas, user stories |
| [`docs/02_UX`](docs/02_UX/ux.md) | Flows, IA, design system, accessibility |
| [`docs/03_System_Design`](docs/03_System_Design/system-design.md) | Architecture, data flows, deployment topology |
| [`docs/04_API`](docs/04_API/api-spec.md) | Every endpoint — method, body, response, errors |
| [`docs/05_Database`](docs/05_Database/database.md) | Tables, relationships, indexes, backups |
| [`docs/06_AI`](docs/06_AI/ai-architecture.md) | Parsing, chunking, RAG pipeline, prompts |
| [`docs/07_Security`](docs/07_Security/security.md) | Auth, secrets, injection defenses, OWASP checklist |
| [`docs/08_DevOps`](docs/08_DevOps/devops.md) | Environments, CI/CD, monitoring, backups |
| [`docs/09_Sprints`](docs/09_Sprints/sprint-plan.md) | Sprint-by-sprint breakdown, risk register |
| [`docs/10_Meeting_Notes`](docs/10_Meeting_Notes/) | Dated meeting logs |
| [`docs/ADR`](docs/ADR/) | Why we made each structural decision |

## Roadmap (5 Phases)

1. **Foundation & Setup** — auth, DB schema, frontend shell, RAG spike
2. **Ingestion & Retrieval Core** — upload, parsing, chunking, embeddings, Notes UI
3. **RAG Chat Experience** — full RAG pipeline, chat UI, PDF viewer
4. **AI Feature Expansion** — summarizer, quiz/flashcards, planner, analytics
5. **Hardening, QA & Deployment** — security pass, testing, CI/CD, deploy

## License

MIT — see [`LICENSE`](LICENSE).
# studysage
