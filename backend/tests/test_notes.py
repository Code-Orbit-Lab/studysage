"""
Notes/upload endpoint tests. Owner: Sumit.
Requires a running Postgres with migrations applied. No AI Service needs
to be running — these tests specifically also verify the upload endpoint
degrades gracefully (marks a document 'failed') when it isn't.
"""
import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from database.session import SessionLocal
from main import app
from models import User

client = TestClient(app)

TEST_EMAIL = "notes-test-user@example.com"
OTHER_EMAIL = "notes-test-other@example.com"
PASSWORD = "supersecret123"


def _make_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n%%EOF"


def _make_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", "<xml>test</xml>")
    return buf.getvalue()


def _make_pptx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ppt/presentation.xml", "<xml>test</xml>")
    return buf.getvalue()


def _cleanup_test_users():
    db = SessionLocal()
    db.query(User).filter(User.email.in_([TEST_EMAIL, OTHER_EMAIL])).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers():
    """Registers a fresh test user and returns Authorization headers.
    Cleanup here also covers OTHER_EMAIL so other_user_headers below
    always starts clean."""
    _cleanup_test_users()
    r = client.post("/auth/register", json={"email": TEST_EMAIL, "password": PASSWORD, "name": "Notes Tester"})
    token = r.json()["access_token"]
    yield {"Authorization": f"Bearer {token}"}
    _cleanup_test_users()


@pytest.fixture
def other_user_headers():
    r = client.post("/auth/register", json={"email": OTHER_EMAIL, "password": PASSWORD, "name": "Other User"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_subject(headers):
    r = client.post("/subjects", json={"name": "Data Structures"}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def _upload(subject_id, filename, content, content_type, headers):
    return client.post(
        "/notes/upload",
        data={"subject_id": subject_id},
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


def test_create_and_list_subjects(auth_headers):
    subject_id = _create_subject(auth_headers)
    r = client.get("/subjects", headers=auth_headers)
    assert r.status_code == 200
    assert any(s["id"] == subject_id for s in r.json())


def test_upload_pdf_succeeds(auth_headers):
    subject_id = _create_subject(auth_headers)
    r = _upload(subject_id, "notes.pdf", _make_pdf_bytes(), "application/pdf", auth_headers)
    assert r.status_code == 202
    assert r.json()["status"] == "processing"


def test_upload_docx_detected_by_content_not_extension(auth_headers):
    subject_id = _create_subject(auth_headers)
    r = _upload(subject_id, "notes.docx", _make_docx_bytes(), "application/octet-stream", auth_headers)
    assert r.status_code == 202
    doc_id = r.json()["document_id"]

    got = client.get(f"/notes/{doc_id}", headers=auth_headers)
    assert got.json()["file_type"] == "docx"


def test_upload_pptx_detected_by_content(auth_headers):
    subject_id = _create_subject(auth_headers)
    r = _upload(subject_id, "slides.pptx", _make_pptx_bytes(), "application/octet-stream", auth_headers)
    assert r.status_code == 202
    doc_id = r.json()["document_id"]

    got = client.get(f"/notes/{doc_id}", headers=auth_headers)
    assert got.json()["file_type"] == "pptx"


def test_upload_rejects_unsupported_type(auth_headers):
    subject_id = _create_subject(auth_headers)
    r = _upload(subject_id, "notes.txt", b"just plain text", "text/plain", auth_headers)
    assert r.status_code == 422


def test_upload_rejects_mislabeled_file():
    """A '.pdf' filename whose bytes are plain text should still be
    rejected — the whole point of content-based detection over trusting
    the extension."""
    from services.file_validation import detect_file_type
    assert detect_file_type(b"not actually a pdf") is None


def test_upload_to_nonexistent_subject_returns_404(auth_headers):
    fake_subject_id = "00000000-0000-0000-0000-000000000000"
    r = _upload(fake_subject_id, "notes.pdf", _make_pdf_bytes(), "application/pdf", auth_headers)
    assert r.status_code == 404


def test_cannot_upload_to_another_users_subject(auth_headers, other_user_headers):
    subject_id = _create_subject(auth_headers)  # owned by TEST_EMAIL
    r = _upload(subject_id, "notes.pdf", _make_pdf_bytes(), "application/pdf", other_user_headers)
    assert r.status_code == 404  # not 403 — existence isn't confirmed either


def test_ai_service_unreachable_marks_document_failed(auth_headers):
    """No AI Service runs in this test environment — proves the upload
    endpoint degrades gracefully instead of hanging or crashing."""
    subject_id = _create_subject(auth_headers)
    r = _upload(subject_id, "notes.pdf", _make_pdf_bytes(), "application/pdf", auth_headers)
    doc_id = r.json()["document_id"]

    got = client.get(f"/notes/{doc_id}", headers=auth_headers)
    assert got.json()["status"] == "failed"


def test_upload_rejects_oversized_file(auth_headers, monkeypatch):
    import api.notes as notes_module
    monkeypatch.setattr(notes_module, "MAX_UPLOAD_SIZE_BYTES", 10)  # tiny limit for this test

    subject_id = _create_subject(auth_headers)
    r = _upload(subject_id, "notes.pdf", _make_pdf_bytes(), "application/pdf", auth_headers)
    assert r.status_code == 413


def test_delete_note(auth_headers):
    subject_id = _create_subject(auth_headers)
    r = _upload(subject_id, "notes.pdf", _make_pdf_bytes(), "application/pdf", auth_headers)
    doc_id = r.json()["document_id"]

    d = client.delete(f"/notes/{doc_id}", headers=auth_headers)
    assert d.status_code == 204

    got = client.get(f"/notes/{doc_id}", headers=auth_headers)
    assert got.status_code == 404