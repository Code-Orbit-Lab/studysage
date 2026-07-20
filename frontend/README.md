# Frontend — StudySage

Next.js app: dashboard, notes manager, chat UI, PDF viewer, quiz UI, settings.

## Setup
```bash
cd frontend
npm install
cp ../.env.example .env.local   # NEXT_PUBLIC_API_URL etc.
npm run dev
```

## Owns
- `app/` — all screens (dashboard, notes, chat, quiz, settings)
- Default scope: Landing, Dashboard, Notes Manager, Settings
- Paired (with Sumit/Saurabh): Chat UI, PDF Viewer, Quiz UI — these are state-heavy,
  build them once the simpler screens are solid

See root `README.md` for the full picture and `/docs` for architecture.
