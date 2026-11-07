"""Tests for settings router endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.auth import get_configured_password
from src.api.main import app

client = TestClient(app)
AUTH_PWD = get_configured_password()
AUTH_HEADERS = {"x-studio-password": AUTH_PWD} if AUTH_PWD else {}


def test_get_settings():
    response = client.get("/api/settings", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "default_model" in data
    assert "available_models" in data
    assert len(data["available_models"]) >= 5
    assert "api_keys_configured" in data


def test_update_settings():
    response = client.post(
        "/api/settings",
        json={
            "default_model": "gemini-3-flash-preview",
            "default_thinking_level": "medium",
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["default_model"] == "gemini-3-flash-preview"
    assert data["default_thinking_level"] == "medium"


@patch("src.api.routers.settings.genai.Client")
def test_test_model_mocked(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="pong")
    mock_client_cls.return_value = mock_client

    response = client.post(
        "/api/settings/test-model",
        json={"model": "gemini-3-flash-preview", "provider": "gemini"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "정상 동작 확인" in data["message"]
    assert data["latency_ms"] >= 0
