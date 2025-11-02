"""Tests for Ollama integration and AI fallback logic."""
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app


client = TestClient(app)


def test_ai_status_endpoint_exists():
    """Test that the AI status endpoint is available."""
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "ollama" in data
    assert "langchain" in data


def test_ai_status_shows_ollama_configuration():
    """Test that AI status shows Ollama configuration."""
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    
    # Check Ollama configuration
    assert "enabled" in data["ollama"]
    assert "url" in data["ollama"]
    assert "available" in data["ollama"]


@patch.dict(os.environ, {"USE_OLLAMA": "true", "OLLAMA_URL": "http://localhost:11434"})
def test_ollama_enabled_in_environment():
    """Test that USE_OLLAMA environment variable is respected."""
    # Import after patching environment
    import importlib
    import backend.main as backend_main
    importlib.reload(backend_main)
    
    # Verify the configuration
    assert backend_main.USE_OLLAMA is True
    assert backend_main.OLLAMA_URL == "http://localhost:11434"


def test_ai_generate_endpoint_exists():
    """Test that the unified AI generate endpoint exists."""
    # This will fail gracefully if no providers are available
    response = client.post("/api/ai/generate", json={
        "prompt": "Hello, world!",
    })
    # Should return either 503 (no providers) or 502 (provider error)
    assert response.status_code in [200, 502, 503]


def test_ollama_health_endpoint():
    """Test Ollama health check endpoint."""
    response = client.get("/api/ollama/health")
    # Will return 200 with ok=false if Ollama is not running, or 502 on connection error
    assert response.status_code in [200, 502]


def test_ollama_models_endpoint():
    """Test Ollama models list endpoint."""
    response = client.get("/api/ollama/models")
    # Will return 502 if Ollama is not available
    assert response.status_code in [200, 502]


@patch('requests.post')
def test_ai_generate_with_ollama_success(mock_post):
    """Test AI generate with successful Ollama response."""
    # Mock successful Ollama response
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "Hello! How can I help you?",
        "model": "qwen3-coder:30b",
        "done": True,
    }
    mock_post.return_value = mock_response
    
    with patch.dict(os.environ, {"USE_OLLAMA": "true"}):
        # Reload module to pick up new environment
        import importlib
        import backend.main as backend_main
        importlib.reload(backend_main)
        test_client = TestClient(backend_main.app)
        
        response = test_client.post("/api/ai/generate", json={
            "prompt": "Hello!",
        })
        
        # Should succeed with mocked response
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "ollama"
        assert data["success"] is True


def test_health_endpoint():
    """Test basic health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
