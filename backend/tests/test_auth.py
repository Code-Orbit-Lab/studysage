"""
Auth endpoint tests — register/login/me/refresh + key edge cases.
Owner: Sumit. Requires a running Postgres with migrations applied
(see README: docker compose up -d && alembic upgrade head).
"""
import pytest
from fastapi.testclient import TestClient

from database.session import SessionLocal
from main import app
from models import User

client = TestClient(app)

TEST_EMAIL = "auth-test-user@example.com"
TEST_PASSWORD = "supersecret123"


@pytest.fixture(autouse=True)
def cleanup_test_user():
    """Remove any leftover test user before and after each test, so the
    suite is rerunnable without manual DB resets."""
    def _delete():
        db = SessionLocal()
        db.query(User).filter(User.email == TEST_EMAIL).delete()
        db.commit()
        db.close()

    _delete()
    yield
    _delete()


def _register():
    return client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": "Test User"},
    )


def test_register_returns_tokens():
    r = _register()
    assert r.status_code == 201
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_duplicate_register_returns_409():
    _register()
    r = _register()
    assert r.status_code == 409


def test_login_with_correct_password():
    _register()
    r = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_with_wrong_password_returns_401():
    _register()
    r = client.post("/auth/login", json={"email": TEST_EMAIL, "password": "wrongpassword"})
    assert r.status_code == 401


def test_me_requires_valid_token():
    r = client.get("/auth/me")
    assert r.status_code in (401, 403)


def test_me_rejects_garbage_token():
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_me_returns_current_user_with_valid_token():
    tokens = _register().json()
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == TEST_EMAIL


def test_refresh_issues_new_access_token():
    tokens = _register().json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new_token = r.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me.status_code == 200


def test_refresh_token_cannot_be_used_as_access_token():
    tokens = _register().json()
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401