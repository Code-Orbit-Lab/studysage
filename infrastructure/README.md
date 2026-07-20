# Infrastructure

Deployment configuration for each service. Local dev only needs
`docker-compose.yml` at the repo root (Postgres) — this folder is for
deployment-time config, added incrementally in Phase 5.

| Service | Platform | Config |
|---|---|---|
| Frontend | Vercel | auto-detects Next.js, no config file needed for v1 |
| Backend | Render | `render.yaml` in this folder |
| AI Service | Render | separate Render service, own `render.yaml` if needed |
| Database + Storage | Supabase | managed, configured via Supabase dashboard |
| Vector DB | ChromaDB (embedded with AI Service) or Qdrant Cloud | no separate infra for the Chroma option |

See [`docs/08_DevOps/devops.md`](../docs/08_DevOps/devops.md) for the full
CI/CD picture.
