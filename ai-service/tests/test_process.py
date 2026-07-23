"""Tests for /process endpoint. Supabase download is mocked - only the
storage-not-configured error path is tested for real, since actual
credentials aren't available yet (see storage.py)."""
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_process_returns_503_when_storage_not_configured():
    response = client.post(
        "/process",
        json={
            "document_id": "doc_1",
            "subject_id": "subj_1",
            "storage_path": "some/path.pdf",
            "file_type": "pdf",
        },
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


@patch("main.download_from_storage")
def test_process_parses_chunks_and_embeds_on_successful_download(mock_download):
    # Point the "downloaded" file at a real sample PDF already in the repo
    sample_pdf = Path(__file__).parent.parent / "spike" / "sample.pdf"
    mock_download.return_value = sample_pdf

    response = client.post(
        "/process",
        json={
            "document_id": "doc_process_test",
            "subject_id": "subj_process_test",
            "storage_path": "fake/path/sample.pdf",
            "file_type": "pdf",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["chunk_count"] > 0


def test_process_rejects_missing_fields():
    response = client.post("/process", json={"document_id": "doc_1"})
    assert response.status_code == 422