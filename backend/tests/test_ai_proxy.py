"""
Tests for the chat/quiz/flashcards/planner proxy endpoints. Owner: Sumit.

No live AI Service is available in this test environment, so each proxied
call is mocked at the ai_client function each router imported — this
verifies our ownership checks, readiness gating, and request/response
translation, independent of Saurabh's actual implementation. The
"unreachable" tests use no mock at all, exercising the real network path
to prove graceful 503s.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

import api.chat as chat_module
import api.flashcards as flashcards_module
import api.planner as planner_module
import api.quiz as quiz_module
from database.session import SessionLocal
from main import app
from models import Document, User

client = TestClient(app)

TEST_EMAIL = "ai-proxy-test@example.com"
OTHER_EMAIL = "ai-proxy-test-other@example.com"
PASSWORD = "supersecret123"


def _cleanup():
    db = SessionLocal()
    db.query(User).filter(User.email.in_([TEST_EMAIL, OTHER_EMAIL])).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers():
    _cleanup()
    r = client.post("/auth/register", json={"email": TEST_EMAIL, "password": PASSWORD, "name": "Tester"})
    token = r.json()["access_token"]
    yield {"Authorization": f"Bearer {token}"}
    _cleanup()


@pytest.fixture
def other_user_headers():
    r = client.post("/auth/register", json={"email": OTHER_EMAIL, "password": PASSWORD, "name": "Other"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_subject(headers, name="DSA"):
    r = client.post("/subjects", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def _make_ready_document(subject_id: str) -> str:
    """Bypasses the real upload+ingestion flow — directly inserts a
    'ready' document row, since these tests are about the proxy layer,
    not re-testing upload (already covered in test_notes.py)."""
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


# ---------- chat ----------

def test_chat_requires_a_ready_document(auth_headers):
    subject_id = _create_subject(auth_headers)
    r = client.post("/chat/query", json={"subject_id": subject_id, "message": "hi"}, headers=auth_headers)
    assert r.status_code == 409  # no ready document yet


def test_chat_proxies_to_ai_service(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    _make_ready_document(subject_id)

    monkeypatch.setattr(
        chat_module,
        "query_ai_service",
        lambda query, sid: {"answer": "It's the powerhouse of the cell.", "citations": [], "flagged_chunks": []},
    )

    r = client.post(
        "/chat/query", json={"subject_id": subject_id, "message": "What is mitochondria?"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert "powerhouse" in r.json()["answer"]


def test_chat_returns_503_when_ai_service_unreachable(auth_headers):
    subject_id = _create_subject(auth_headers)
    _make_ready_document(subject_id)
    r = client.post("/chat/query", json={"subject_id": subject_id, "message": "hi"}, headers=auth_headers)
    assert r.status_code == 503  # nothing mocked, real (failing) network call


def test_chat_rejects_other_users_subject(auth_headers, other_user_headers):
    subject_id = _create_subject(auth_headers)
    r = client.post("/chat/query", json={"subject_id": subject_id, "message": "hi"}, headers=other_user_headers)
    assert r.status_code == 404


# ---------- quiz ----------

def test_quiz_requires_ready_document(auth_headers):
    subject_id = _create_subject(auth_headers)
    db = SessionLocal()
    doc = Document(
        subject_id=uuid.UUID(subject_id), filename="a.pdf", file_type="pdf",
        storage_path="/tmp/a.pdf", status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = str(doc.id)
    db.close()

    r = client.post("/quiz/generate", json={"document_id": doc_id, "question_count": 5}, headers=auth_headers)
    assert r.status_code == 409


def test_quiz_proxies_to_ai_service(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    doc_id = _make_ready_document(subject_id)

    monkeypatch.setattr(
        quiz_module,
        "generate_quiz",
        lambda sid, did, count, types: {"questions": [{"type": "mcq", "question": "...", "answer": "B"}], "question_count": 1},
    )

    r = client.post("/quiz/generate", json={"document_id": doc_id, "question_count": 1}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["question_count"] == 1


def test_quiz_rejects_other_users_document(auth_headers, other_user_headers):
    subject_id = _create_subject(auth_headers)
    doc_id = _make_ready_document(subject_id)
    r = client.post("/quiz/generate", json={"document_id": doc_id}, headers=other_user_headers)
    assert r.status_code == 404


# ---------- flashcards ----------

def test_flashcards_proxies_to_ai_service(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    doc_id = _make_ready_document(subject_id)

    monkeypatch.setattr(
        flashcards_module,
        "generate_flashcards",
        lambda sid, did, count, difficulty: {"flashcards": [{"question": "Q", "answer": "A", "difficulty": "easy"}], "card_count": 1},
    )

    r = client.post("/flashcards/generate", json={"document_id": doc_id, "card_count": 1}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["card_count"] == 1


def test_flashcards_returns_503_when_unreachable(auth_headers):
    subject_id = _create_subject(auth_headers)
    doc_id = _make_ready_document(subject_id)
    r = client.post("/flashcards/generate", json={"document_id": doc_id}, headers=auth_headers)
    assert r.status_code == 503


# ---------- planner ----------

def test_planner_resolves_subject_ids_to_names(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers, name="Operating Systems")

    captured = {}

    def fake_generate_plan(subjects, deadline, hours_per_day, start_date):
        captured["subjects"] = subjects
        return {"plan": [], "days_available": 5}

    monkeypatch.setattr(planner_module, "generate_plan", fake_generate_plan)

    r = client.post(
        "/planner/generate",
        json={
            "subjects": [{"subject_id": subject_id, "priority": 1}],
            "deadline": "2026-08-15",
            "hours_per_day": 3,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    # the AI service only understands names, never sees our subject_id
    assert captured["subjects"] == [{"name": "Operating Systems", "priority": 1}]


def test_planner_rejects_other_users_subject(auth_headers, other_user_headers):
    subject_id = _create_subject(auth_headers)
    r = client.post(
        "/planner/generate",
        json={"subjects": [{"subject_id": subject_id, "priority": 1}], "deadline": "2026-08-15", "hours_per_day": 3},
        headers=other_user_headers,
    )
    assert r.status_code == 404