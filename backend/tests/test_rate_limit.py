"""Tests that the LLM-backed endpoints are rate-limited per user
(20/minute, see services/rate_limit.py). Owner: Sumit.
"""
import pytest
from fastapi.testclient import TestClient

from database.session import SessionLocal
from main import app
from models import User

client = TestClient(app)

TEST_EMAIL = "rate-limit-test@example.com"
OTHER_EMAIL = "rate-limit-test-other@example.com"
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


def _create_subject(headers, name="DSA"):
    r = client.post("/subjects", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def test_planner_generate_returns_429_after_20_requests_per_minute(auth_headers):
    subject_id = _create_subject(auth_headers)
    body = {"subjects": [{"subject_id": subject_id, "priority": 1}], "deadline": "2026-08-15", "hours_per_day": 3}

    # statuses = [client.post("/planner/generate", json=body, headers=auth_headers).status_code for _ in range(21)]
    
    responses = [
        client.post("/planner/generate", json=body, headers=auth_headers)
        for _ in range(21)
    ]

    for i, r in enumerate(responses, 1):
        print(f"{i:02d}: {r.status_code} -> {r.text}")

    statuses = [r.status_code for r in responses]

    # first 20 hit the real (unmocked, failing) AI service -> 503; the
    # 21st should be rejected by the limiter before it even tries -> 429
    assert statuses[:20].count(503) == 20
    assert statuses[20] == 429


def test_rate_limit_is_scoped_per_user(auth_headers):
    """A different user's requests shouldn't be blocked by someone else
    exhausting their own limit."""
    subject_id = _create_subject(auth_headers)
    body = {"subjects": [{"subject_id": subject_id, "priority": 1}], "deadline": "2026-08-15", "hours_per_day": 3}
    for _ in range(21):
        client.post("/planner/generate", json=body, headers=auth_headers)

    r_other = client.post("/auth/register", json={"email": OTHER_EMAIL, "password": PASSWORD, "name": "Other"})
    other_headers = {"Authorization": f"Bearer {r_other.json()['access_token']}"}
    other_subject_id = _create_subject(other_headers, name="Other Subject")
    other_body = {"subjects": [{"subject_id": other_subject_id, "priority": 1}], "deadline": "2026-08-15", "hours_per_day": 3}

    r = client.post("/planner/generate", json=other_body, headers=other_headers)
    assert r.status_code == 503  # not 429 -- this user still has their own fresh bucket
