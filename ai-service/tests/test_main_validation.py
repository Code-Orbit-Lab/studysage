"""Request validation tests for main.py endpoints - checks that FastAPI/Pydantic
reject malformed requests before they reach the generator functions."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_query_rejects_empty_query():
    response = client.post("/query", json={"query": "", "subject_id": "test"})
    assert response.status_code == 422


def test_query_rejects_whitespace_only_query():
    response = client.post("/query", json={"query": "   ", "subject_id": "test"})
    assert response.status_code == 422


def test_query_rejects_oversized_query():
    response = client.post("/query", json={"query": "x" * 3000, "subject_id": "test"})
    assert response.status_code == 422


def test_quiz_rejects_question_count_out_of_range():
    response = client.post(
        "/quiz",
        json={"subject_id": "test", "document_id": "test", "question_count": 50},
    )
    assert response.status_code == 422


def test_flashcards_rejects_zero_card_count():
    response = client.post(
        "/flashcards",
        json={"subject_id": "test", "document_id": "test", "card_count": 0},
    )
    assert response.status_code == 422


def test_planner_rejects_zero_hours_per_day():
    response = client.post(
        "/planner",
        json={
            "subjects": [{"name": "Math", "priority": 1}],
            "deadline": "2026-12-01",
            "hours_per_day": 0,
        },
    )
    assert response.status_code == 422


def test_planner_rejects_empty_subjects_list():
    response = client.post(
        "/planner",
        json={"subjects": [], "deadline": "2026-12-01", "hours_per_day": 2},
    )
    assert response.status_code == 422