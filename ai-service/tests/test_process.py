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


@patch("main.download_from_storage")
def test_process_handles_generic_image_file_type(mock_download, tmp_path):
    """Confirms the file_type='image' value from backend's content-sniffed
    detection (file_validation.py detect_file_type()) is accepted - not
    just literal png/jpg/jpeg. This is the ACTUAL value the real upload
    flow sends for any photographed page, since Sumit's backend
    deliberately doesn't distinguish jpg vs png (security: content-sniffed,
    not extension-trusted)."""
    from PIL import Image, ImageDraw

    img_path = tmp_path / "downloaded_photo"  # no extension, matches real flow
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "STUDY NOTES SAMPLE TEXT", fill="black")
    img.save(img_path, format="JPEG")
    mock_download.return_value = img_path

    response = client.post(
        "/process",
        json={
            "document_id": "doc_image_type_test",
            "subject_id": "subj_image_type_test",
            "storage_path": "fake/path/photo",
            "file_type": "image",
        },
    )
    assert response.status_code == 422
    assert "no extractable text" in response.json()["detail"].lower()