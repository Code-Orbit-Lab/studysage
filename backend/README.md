# Backend — StudySage

FastAPI service: auth, notes/upload/analytics APIs, orchestration with the AI service.

## Setup
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in real values
uvicorn main:app --reload --port 8000
```

## Owns
- `auth/` — JWT + Google OAuth, email verify, password reset
- `api/` — notes, upload, analytics endpoints
- `database/` — SQLAlchemy models + Alembic migrations
- `services/` — glue logic calling the AI service

See root `README.md` for the full picture and `/docs` for architecture.
