"""Tests that the chat/quiz/flashcards/planner endpoints actually persist
rows (chat_messages, quizzes+quiz_questions, quiz_attempts, flashcards,
study_plans), and that quiz submission scores correctly. Owner: Sumit.
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
from models import ChatMessage, Flashcard, Quiz, QuizAttempt, QuizQuestion, StudyPlan, User, Document

client = TestClient(app)

TEST_EMAIL = "persistence-test@example.com"
PASSWORD = "supersecret123"


def _cleanup():
    db = SessionLocal()
    db.query(User).filter(User.email == TEST_EMAIL).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers():
    _cleanup()
    r = client.post("/auth/register", json={"email": TEST_EMAIL, "password": PASSWORD, "name": "Tester"})
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
        subject_id=uuid.UUID(subject_id), filename="notes.pdf", file_type="pdf",
        storage_path="/tmp/fake.pdf", status="ready",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = str(doc.id)
    db.close()
    return doc_id


def test_chat_query_persists_both_turns(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    _make_ready_document(subject_id)
    monkeypatch.setattr(
        chat_module, "query_ai_service",
        lambda query, sid: {"answer": "It's the powerhouse of the cell.", "citations": [{"document_id": "x", "page": 1, "snippet": "..."}]},
    )

    r = client.post("/chat/query", json={"subject_id": subject_id, "message": "What is mitochondria?"}, headers=auth_headers)
    assert r.status_code == 200

    db = SessionLocal()
    messages = db.query(ChatMessage).filter(ChatMessage.subject_id == uuid.UUID(subject_id)).order_by(ChatMessage.created_at).all()
    db.close()
    assert len(messages) == 2
    assert messages[0].role == "user" and messages[0].content == "What is mitochondria?"
    assert messages[1].role == "assistant" and "powerhouse" in messages[1].content
    assert messages[1].citations == [{"document_id": "x", "page": 1, "snippet": "..."}]


def test_chat_query_persists_nothing_on_ai_failure(auth_headers):
    subject_id = _create_subject(auth_headers)
    _make_ready_document(subject_id)
    r = client.post("/chat/query", json={"subject_id": subject_id, "message": "hi"}, headers=auth_headers)
    assert r.status_code == 503

    db = SessionLocal()
    count = db.query(ChatMessage).filter(ChatMessage.subject_id == uuid.UUID(subject_id)).count()
    db.close()
    assert count == 0


def test_chat_history_returns_persisted_turns_in_order(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    _make_ready_document(subject_id)
    monkeypatch.setattr(chat_module, "query_ai_service", lambda q, sid: {"answer": "A1", "citations": []})
    client.post("/chat/query", json={"subject_id": subject_id, "message": "Q1"}, headers=auth_headers)

    r = client.get(f"/chat/history?subject_id={subject_id}", headers=auth_headers)
    assert r.status_code == 200
    history = r.json()
    assert len(history) == 2
    assert history[0]["role"] == "user" and history[0]["content"] == "Q1"
    assert history[1]["role"] == "assistant" and history[1]["content"] == "A1"


def test_quiz_generate_persists_quiz_and_questions(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    doc_id = _make_ready_document(subject_id)
    monkeypatch.setattr(
        quiz_module, "generate_quiz",
        lambda sid, did, count, types: {
            "questions": [
                {"type": "mcq", "question": "2+2?", "options": ["3", "4"], "answer": "4"},
                {"type": "true_false", "question": "Sky is blue", "answer": "true"},
            ],
            "question_count": 2,
        },
    )
    r = client.post("/quiz/generate", json={"document_id": doc_id, "question_count": 2}, headers=auth_headers)
    assert r.status_code == 200
    quiz_id = r.json()["quiz_id"]

    db = SessionLocal()
    quiz = db.query(Quiz).filter(Quiz.id == uuid.UUID(str(quiz_id))).first()
    assert quiz is not None
    assert quiz.subject_id == uuid.UUID(subject_id)
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).all()
    db.close()
    assert len(questions) == 2
    assert {q.type for q in questions} == {"mcq", "true_false"}


def test_quiz_submit_scores_and_persists_attempt(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    doc_id = _make_ready_document(subject_id)
    monkeypatch.setattr(
        quiz_module, "generate_quiz",
        lambda sid, did, count, types: {
            "questions": [
                {"type": "mcq", "question": "2+2?", "options": ["3", "4"], "answer": "4"},
                {"type": "true_false", "question": "Sky is blue", "answer": "true"},
            ],
        },
    )
    gen = client.post("/quiz/generate", json={"document_id": doc_id, "question_count": 2}, headers=auth_headers)
    quiz_id = gen.json()["quiz_id"]
    q_ids = [q["id"] for q in gen.json()["questions"]]

    # answer the first correctly, second incorrectly
    answers = {q_ids[0]: "4", q_ids[1]: "false"}
    r = client.post(f"/quiz/{quiz_id}/submit", json={"answers": answers}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 1
    assert body["total"] == 2

    db = SessionLocal()
    attempt = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == uuid.UUID(str(quiz_id))).first()
    db.close()
    assert attempt is not None
    assert attempt.score == 1 and attempt.total == 2


def test_flashcards_generate_persists_cards(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers)
    doc_id = _make_ready_document(subject_id)
    monkeypatch.setattr(
        flashcards_module, "generate_flashcards",
        lambda sid, did, count, difficulty: {
            "flashcards": [{"question": "Q1", "answer": "A1", "difficulty": "easy"}],
            "card_count": 1,
        },
    )
    r = client.post("/flashcards/generate", json={"document_id": doc_id, "card_count": 1}, headers=auth_headers)
    assert r.status_code == 200

    db = SessionLocal()
    cards = db.query(Flashcard).filter(Flashcard.subject_id == uuid.UUID(subject_id)).all()
    db.close()
    assert len(cards) == 1
    assert cards[0].question == "Q1" and cards[0].answer == "A1"


def test_planner_generate_persists_study_plan(auth_headers, monkeypatch):
    subject_id = _create_subject(auth_headers, name="Operating Systems")
    monkeypatch.setattr(
        planner_module, "generate_plan",
        lambda subjects, deadline, hours_per_day, start_date: {"plan": [{"day": 1, "date": "2026-08-01", "sessions": []}], "days_available": 5},
    )
    r = client.post(
        "/planner/generate",
        json={"subjects": [{"subject_id": subject_id, "priority": 1}], "deadline": "2026-08-15", "hours_per_day": 3},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert "study_plan_id" in r.json()

    db = SessionLocal()
    plans = db.query(StudyPlan).all()
    db.close()
    assert any(str(p.id) == r.json()["study_plan_id"] for p in plans)