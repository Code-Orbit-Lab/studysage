# Security — StudySage

## Authentication & Authorization
- JWT access tokens (short-lived) + refresh tokens; validated on every
  protected route in the Backend.
- Passwords hashed with bcrypt (`passlib`) — never stored or logged in
  plain text.
- Google OAuth verified server-side against Google's token endpoint, not
  trusted from the client alone.
- A user can only read/write their own subjects/documents/chat — every
  query filters by `user_id` derived from the JWT, never from a client-
  supplied field.

## Secrets Management
- `.env` files are gitignored; `.env.example` documents the shape with
  placeholder values only.
- Real secrets (DB URL, JWT secret, Gemini API key, OAuth credentials) live
  in GitHub Actions Secrets and each platform's environment settings.

## Injection & Web Vulnerabilities
- **SQL injection:** SQLAlchemy ORM/parameterized queries only — no raw
  string-built SQL.
- **XSS:** Chat/notes content is rendered as sanitized markdown on the
  frontend, not raw HTML.
- **CSRF:** JWT-in-header auth (not cookies) sidesteps classic CSRF; if
  cookies are introduced later, add CSRF tokens then.

## Rate Limiting
- `/chat/query`, `/quiz/generate`, `/flashcards/generate`,
  `/planner/generate` are rate-limited per user (LLM-cost-sensitive
  endpoints) — see limits noted in [API Spec](../04_API/api-spec.md).

## File Upload Security
- Validate file type by content (not just extension) before parsing.
- Enforce a max file size.
- Parse in an isolated step so a malformed file can't crash the whole AI
  Service — catch and mark the document `failed` instead.

## Prompt Injection / RAG Security
- Uploaded document text is treated as **data**, never as instructions —
  the system prompt explicitly tells the model to ignore any instructions
  found inside retrieved chunks.
- User chat input is similarly never concatenated into the system prompt
  unescaped.

## Data Privacy
- A user's uploaded documents and chat history are private to that user by
  default — no cross-user retrieval, no admin dashboard reading document
  contents in v1.
- Deleting a document removes both the file (Storage) and its vectors
  (Vector DB), not just the metadata row.

## Audit Logging
- Auth events (login, failed login, password reset) logged with timestamp
  + user ID, no plaintext credentials in logs.

## Checklist (OWASP-flavored, v1 scope)
- [x] Broken access control — per-user filtering on every query
- [x] Injection — ORM everywhere, no raw SQL
- [x] Auth — bcrypt + JWT, verified OAuth
- [x] Data exposure — secrets never committed, .env gitignored
- [ ] Security logging/monitoring — basic in v1, revisit in Phase 5
- [ ] Rate limiting on all endpoints (currently on the LLM-cost ones — extend to auth endpoints in Phase 5)
