"""
HTTP client for calling the AI Service. Owner: Sumit.
Contract: docs/06_AI/ai-architecture.md#backend--ai-service-contract.
"""
import os

import httpx

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
_TIMEOUT = httpx.Timeout(10.0, connect=3.0)


def trigger_processing(document_id: str, subject_id: str, storage_path: str, file_type: str) -> bool:
    """
    Calls the AI Service to parse/chunk/embed a document. Returns True if
    it accepted and completed processing, False on any failure
    (unreachable, timeout, non-200) — caller marks the document 'failed'
    in that case rather than raising, so an AI Service outage doesn't
    take the upload endpoint down with it.
    """
    try:
        response = httpx.post(
            f"{AI_SERVICE_URL}/process",
            json={
                "document_id": document_id,
                "subject_id": subject_id,
                "storage_path": storage_path,
                "file_type": file_type,
            },
            timeout=_TIMEOUT,
        )
        return response.status_code == 200
    except httpx.HTTPError:
        return False

def _post(path: str, payload: dict) -> dict | None:
    """Shared POST helper for the AI Service's generation endpoints —
    returns the parsed JSON body on 200, None on any failure (unreachable,
    timeout, non-200). Callers turn None into a 503 for the caller."""
    try:
        response = httpx.post(f"{AI_SERVICE_URL}{path}", json=payload, timeout=_TIMEOUT)
        if response.status_code != 200:
            return None
        return response.json()
    except httpx.HTTPError:
        return None


def query_ai_service(query: str, subject_id: str) -> dict | None:
    return _post("/query", {"query": query, "subject_id": subject_id})


def summarize_document(subject_id: str, document_id: str, length: str) -> dict | None:
    return _post("/summarize", {"subject_id": subject_id, "document_id": document_id, "length": length})


def generate_quiz(subject_id: str, document_id: str, question_count: int, types: list[str]) -> dict | None:
    return _post(
        "/quiz",
        {
            "subject_id": subject_id,
            "document_id": document_id,
            "question_count": question_count,
            "types": types,
        },
    )


def generate_flashcards(subject_id: str, document_id: str, card_count: int, difficulty: str) -> dict | None:
    return _post(
        "/flashcards",
        {"subject_id": subject_id, "document_id": document_id, "card_count": card_count, "difficulty": difficulty},
    )


def generate_plan(
    subjects: list[dict], deadline: str, hours_per_day: float, start_date: str | None
) -> dict | None:
    payload = {"subjects": subjects, "deadline": deadline, "hours_per_day": hours_per_day}
    if start_date:
        payload["start_date"] = start_date
    return _post("/planner", payload)