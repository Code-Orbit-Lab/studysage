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

def test_process_rejects_invalid_file_type():
    response = client.post(
        "/process",
        json={
            "document_id": "doc_1",
            "subject_id": "subj_1",
            "storage_path": "some/path.xyz",
            "file_type": "xyz",
        },
    )
    assert response.status_code == 422


@patch("main.download_from_storage")
def test_process_handles_docx_with_mismatched_suffix(mock_download, tmp_path):
    """Simulates storage returning a file with no/wrong extension - the
    endpoint should still correctly route to the DOCX parser based on
    file_type, not whatever suffix the download happened to have."""
    from docx import Document as DocxDocument

    # Build a minimal real DOCX so parse_docx() has something valid to read
    fake_download_path = tmp_path / "downloaded_file"  # no extension at all
    doc = DocxDocument()
    doc.add_paragraph("This is a test paragraph for the process endpoint DOCX test.")
    doc.save(fake_download_path)

    mock_download.return_value = fake_download_path

    response = client.post(
        "/process",
        json={
            "document_id": "doc_process_docx_test",
            "subject_id": "subj_process_docx_test",
            "storage_path": "fake/path/no_extension_file",
            "file_type": "docx",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["chunk_count"] > 0


"""File retrieval for /process — local disk (current) + Supabase Storage
(future). Owner: Saurabh

Sumit's backend currently stores uploads on local disk (see
backend/services/storage.py docstring: "v1 uses the local filesystem...").
storage_path values are therefore local filesystem paths, not Supabase keys,
for now. This only works when ai-service and backend run on the same
machine/filesystem - genuinely fine for local dev (how the team currently
runs things), but NOT how this will work once either service is
containerized/deployed separately (see infrastructure/render.yaml).
Flagged to Sumit as an open question - not urgent, but a real one.

get_document() checks local disk first; if the path doesn't exist there,
falls back to attempting Supabase Storage (still unconfigured - fails with
a clear 503 until real credentials are wired in). This means once Supabase
IS configured, this file's behavior transitions automatically with zero
changes needed elsewhere.
"""

def test_process_uses_local_disk_when_file_exists_there(tmp_path):
    """Confirms the local-disk fallback works without any Supabase mocking -
    this is the actual current path Sumit's backend exercises today."""
    sample_pdf = Path(__file__).parent.parent / "spike" / "sample.pdf"
    local_copy = tmp_path / "uploaded_sample.pdf"
    local_copy.write_bytes(sample_pdf.read_bytes())

    response = client.post(
        "/process",
        json={
            "document_id": "doc_local_disk_test",
            "subject_id": "subj_local_disk_test",
            "storage_path": str(local_copy),
            "file_type": "pdf",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["chunk_count"] > 0