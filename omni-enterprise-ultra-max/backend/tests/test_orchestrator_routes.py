import os
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient

# Prefer Ollama off for deterministic tests
os.environ.setdefault("USE_OLLAMA", "false")

from main import app

client = TestClient(app)


def test_orchestrator_health():
    resp = client.get("/api/orchestrator/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"
    assert "timestamp" in data


def test_orchestrate_minimal():
    # When brain adapter or ollama is unavailable in test env,
    # the endpoint should still respond with a structured object
    resp = client.post(
        "/api/orchestrate",
        json={
            "query": "Say hello",
            "tenant_id": "test-tenant",
            "user_id": "user@example.com",
            "provider": "auto",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("module") == "ai.chat"
    assert data.get("tenant_id") == "test-tenant"
    assert "execution_time" in data
    assert "timestamp" in data
