# DevOps — StudySage

## Environments
| Env | Purpose | Trigger |
|---|---|---|
| Local | Development | `docker compose up -d` (Postgres) + run each service manually |
| Staging | Integration testing before a phase demo | Auto-deploy on merge to `develop` |
| Production | Live | Auto-deploy on merge to `main` |

## Docker
`docker-compose.yml` at the repo root runs local Postgres only — each
service (backend/frontend/ai-service) is run directly (`uvicorn`, `npm run
dev`) rather than containerized in dev, to keep hot-reload fast. Container
images for each service get added in `infrastructure/` if/when we containerize
for deployment (see [`infrastructure/README.md`](../../infrastructure/README.md)).

## CI/CD (GitHub Actions)
Three independent workflows, one per service, path-filtered so a frontend
change doesn't trigger a backend test run:
- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/ai-ci.yml`

Each: lint → test on every PR. Deploy steps are handled by the hosting
platforms' own GitHub integration (Vercel/Render auto-deploy on push to
`main`), not by a custom deploy job — simplest option for a 3-person team.

## Monitoring & Logging
v1 keeps this lightweight: platform-native logs (Render/Vercel dashboards)
and Supabase's built-in DB metrics. Revisit with a dedicated tool (e.g. a
free-tier error tracker) only if it becomes a real pain point — not worth
the setup cost before the product itself works end-to-end.

## Scaling Notes
Each service scales independently since they're separate deployments:
- Frontend — Vercel scales automatically.
- Backend/AI Service — start on a single instance each; move to
  autoscaling only if real usage demands it.
- Vector DB — ChromaDB embedded is fine at student-project scale; migrate
  to Qdrant Cloud if a collection grows large enough to need it.

## Backup & Disaster Recovery
- Database: Supabase automated backups (see [Database](../05_Database/database.md#backup-strategy)).
- Code: GitHub is the source of truth; `main` is always deployable, so a
  bad deploy is a revert-and-redeploy, not a recovery project.
