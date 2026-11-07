"""Tests for Langfuse observability tracing in LLMClient and Observability module."""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

import src.observability as obs_mod
from src.extraction.llm_client import LLMClient
from src.observability import flush_langfuse, get_langfuse, trace_observation


class DummySchema(BaseModel):
    message: str


def test_get_langfuse_disabled_by_default(monkeypatch):
    """When LANGFUSE keys are not present in env, get_langfuse returns None."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    obs_mod._client_initialized = False
    obs_mod._langfuse_client = None

    client = get_langfuse()
    assert client is None


def test_trace_observation_no_op_when_disabled(monkeypatch):
    """When Langfuse is disabled, trace_observation yields None without errors."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    obs_mod._client_initialized = False
    obs_mod._langfuse_client = None

    with trace_observation("test-span", as_type="span", input_data={"q": 1}) as obs:
        assert obs is None


def test_llm_client_without_langfuse(monkeypatch):
    """LLMClient works completely normally when Langfuse is not enabled."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    obs_mod._client_initialized = False
    obs_mod._langfuse_client = None

    client = LLMClient(provider="gemini", api_key="dummy-key")
    client._adapter = MagicMock()
    client._adapter.generate_text_sync.return_value = "Generated text"

    result = client.generate_text_sync("System prompt", "User prompt", task_type="test_task")
    assert result == "Generated text"


def test_trace_observation_hierarchical_when_active():
    """When Langfuse is active, trace_observation invokes start_as_current_observation."""
    mock_lf = MagicMock()
    mock_span = MagicMock()
    mock_lf.start_as_current_observation.return_value.__enter__.return_value = mock_span

    obs_mod._client_initialized = True
    obs_mod._langfuse_client = mock_lf

    try:
        with trace_observation("parent-span", as_type="span", input_data={"topic": "ai"}) as span:
            assert span == mock_span
            mock_span.update(output={"status": "done"})

        mock_lf.start_as_current_observation.assert_called_once()
        call_kwargs = mock_lf.start_as_current_observation.call_args.kwargs
        assert call_kwargs["name"] == "parent-span"
        assert call_kwargs["as_type"] == "span"
        assert call_kwargs["input"] == {"topic": "ai"}
        mock_span.update.assert_called_with(output={"status": "done"})
    finally:
        obs_mod._client_initialized = False
        obs_mod._langfuse_client = None


def test_trace_observation_records_error_on_exception():
    """When an exception occurs inside trace_observation, level='ERROR' is updated."""
    mock_lf = MagicMock()
    mock_span = MagicMock()
    mock_lf.start_as_current_observation.return_value.__enter__.return_value = mock_span

    obs_mod._client_initialized = True
    obs_mod._langfuse_client = mock_lf

    try:
        with pytest.raises(ValueError, match="Failed inside"):
            with trace_observation("error-span", as_type="span"):
                raise ValueError("Failed inside")

        mock_span.update.assert_called_with(level="ERROR", status_message="Failed inside")
    finally:
        obs_mod._client_initialized = False
        obs_mod._langfuse_client = None


def test_llm_client_updates_trace_observation():
    """LLMClient updates observation with usage, cost, and output."""
    mock_lf = MagicMock()
    mock_gen = MagicMock()
    mock_lf.start_as_current_observation.return_value.__enter__.return_value = mock_gen

    obs_mod._client_initialized = True
    obs_mod._langfuse_client = mock_lf

    try:
        client = LLMClient(provider="gemini", api_key="dummy-key")
        client._adapter = MagicMock()
        client._adapter.generate_text_sync.return_value = "Draft content"

        res = client.generate_text_sync(
            system_prompt="System",
            user_prompt="User",
            task_type="blueprint_planning",
        )
        assert res == "Draft content"

        mock_gen.update.assert_called_once()
        update_kwargs = mock_gen.update.call_args.kwargs
        assert update_kwargs["output"] == "Draft content"
        assert "usage_details" in update_kwargs
        assert "cost_details" in update_kwargs
        assert "latency_ms" in update_kwargs["metadata"]
    finally:
        obs_mod._client_initialized = False
        obs_mod._langfuse_client = None
        flush_langfuse()
