"""
Smoke test — confirms all three services are up and reachable.
Run with all services running locally (see scripts/setup.sh + README.md).

    pytest tests/integration/test_health_checks.py
"""
import httpx

SERVICES = {
    "backend": "http://localhost:8000/health",
    "ai-service": "http://localhost:8001/health",
}


def test_services_are_up():
    for name, url in SERVICES.items():
        resp = httpx.get(url, timeout=5)
        assert resp.status_code == 200, f"{name} did not respond healthy"
