"""Per-user rate limiting via slowapi, for the LLM-backed proxy endpoints
(chat/quiz/flashcards/planner) — keeps a runaway client (or script) from
burning through the Gemini quota / cost budget. Owner: Sumit

Single Render web-service instance today (see infrastructure/render.yaml),
so slowapi's default in-memory storage is enough. If this ever moves to
more than one instance, in-memory buckets stop being shared across
processes and the limit becomes "N per instance" instead of "N total" --
at that point, point slowapi at Redis instead:
    Limiter(key_func=_rate_limit_key, storage_uri=os.getenv("REDIS_URL"))
"""

from fastapi import Request
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth.security import decode_token


def _rate_limit_key(request: Request) -> str:
    """Buckets by authenticated user id when a valid bearer token is
    present, falling back to remote IP otherwise. This only needs to be
    "good enough" to pick a bucket -- the route's own get_current_user
    dependency is what actually rejects bad/missing tokens with a 401."""
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer ") :]
        try:
            payload = decode_token(token)
        except JWTError:
            payload = None

        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"

    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_rate_limit_key)

# LLM cost control — same budget for all four generation endpoints per
# docs/04_API/api-spec.md (chat/query: "20 requests/minute/user").
LLM_ENDPOINT_LIMIT = "20/minute"
