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