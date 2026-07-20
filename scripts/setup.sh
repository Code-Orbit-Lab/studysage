#!/usr/bin/env bash
# Bootstrap all three services for local development.
set -e

echo "==> Starting local Postgres"
docker compose up -d

echo "==> Backend"
(cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt)

echo "==> AI Service"
(cd ai-service && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt)

echo "==> Frontend"
(cd frontend && npm install)

echo "==> Done. Copy .env.example to .env and fill in real values, then run each service — see README.md"
