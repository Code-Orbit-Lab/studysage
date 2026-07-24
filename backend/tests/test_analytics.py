"""Tests for GET /analytics/progress. Owner: Sumit."""

import uuid

import pytest
from fastapi.testclient import TestClient

import api.quiz as quiz_module
from database.session import SessionLocal
from main import app
from models import Document, User

client = TestClient(app)

TEST_EMAIL = "analytics-test@example.com"
PASSWORD = "supersecret123"


def _cleanup():
    db = SessionLocal()
    db.query(User).filter(User.email == TEST_EMAIL).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers():
    _cleanup()
    r = client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": PASSWORD, "name": "Tester"},
    )
    token = r.json()["access_token"]
    yield {"Authorization": f"Bearer {token}"}
    _cleanup()


def _create_subject(headers, name="DSA"):
    r = client.post("/subjects", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def _make_ready_document(subject_id: str) -> str:
    db = SessionLocal()
    doc = Document(
        subject_id=uuid.UUID(subject_id),
        filename="notes.pdf",
        file_type="pdf",
        storage_path="/tmp/fake.pdf",
        status="ready",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = str(doc.id)
    db.close()
    return doc_id


def test_progress_with_no_activity(auth_headers):
    _create_subject(auth_headers)
    r = client.get("/analytics/progress", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["subjects_covered"] == 1
    assert body["quiz_avg_score"] is None
    assert body["weak_topics"] == []


def test_progress_reflects_quiz_attempts(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers, name="Weak Subject")
    doc_id = _make_ready_document(subject_id)
    monkeypatch.setattr(
        quiz_module,
        "generate_quiz",
        lambda sid, did, count, types: {
            "questions": [
                {
                    "type": "mcq",
                    "question": "2+2?",
                    "options": ["3", "4"],
                    "answer": "4",
                },
                {"type": "true_false", "question": "Sky is blue", "answer": "true"},
            ],
        },
    )
    gen = client.post(
        "/quiz/generate",
        json={"document_id": doc_id, "question_count": 2},
        headers=auth_headers,
    )
    quiz_id = gen.json()["quiz_id"]
    q_ids = [q["id"] for q in gen.json()["questions"]]

    # get 0/2 -- should show up as a weak topic
    client.post(
        f"/quiz/{quiz_id}/submit",
        json={"answers": {q_ids[0]: "3", q_ids[1]: "false"}},
        headers=auth_headers,
    )

    r = client.get("/analytics/progress", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["quiz_avg_score"] == 0.0
    assert "Weak Subject" in body["weak_topics"]
