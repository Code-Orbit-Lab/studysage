"""Shared helpers for Gemini API calls used across rag/, summarizer/, quiz/,
flashcards/, planner/. Owner: Saurabh

Centralizes two things:
1. Wrapping every generate_content() call so ANY Gemini API failure (rate
   limits, permission errors, timeouts) surfaces as a clean RuntimeError
   instead of a raw google.api_core/grpc exception leaking all the way up
   to the FastAPI endpoint. We hit both PermissionDenied and ResourceExhausted
   from live Gemini calls during development - this is not a hypothetical.
2. Truncating oversized document content before it's sent in a prompt, so a
   single very large upload doesn't cause unbounded cost/latency.
"""
import google.api_core.exceptions as google_exceptions

MAX_CONTENT_CHARS = 100_000  # conservative cap (~25k tokens), leaves headroom
                              # for prompt/schema instructions + response


def truncate_content(text: str, max_chars: int = MAX_CONTENT_CHARS) -> str:
    """Truncates document content for very large uploads. This is a stopgap,
    not a real fix for huge documents - a proper fix would chunk-then-summarize
    for oversized docs, worth revisiting if this becomes a real user need."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... content truncated due to length ...]"


def safe_generate_content(model, *args, **kwargs):
    """Calls model.generate_content(...) and converts ANY failure (rate
    limits, permission errors, timeouts, network issues) into a RuntimeError
    with a clean message - never lets a raw Gemini/gRPC exception escape
    past this boundary to the API layer."""
    try:
        return model.generate_content(*args, **kwargs)
    except google_exceptions.GoogleAPIError as e:
        raise RuntimeError(f"AI generation service error: {e}") from e
    except Exception as e:
        # Catch-all: some failures (e.g. raw grpc errors) aren't always
        # wrapped by google.api_core - still shouldn't leak past here.
        raise RuntimeError(f"AI generation failed unexpectedly: {e}") from e