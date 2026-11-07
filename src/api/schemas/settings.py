"""Pydantic schemas for studio settings and configuration API."""

from pydantic import BaseModel


class ModelInfoItem(BaseModel):
    id: str
    name: str
    provider: str
    badge: str
    description: str


class SettingsResponse(BaseModel):
    default_model: str
    default_provider: str
    default_thinking_level: str
    available_models: list[ModelInfoItem]
    api_keys_configured: dict[str, bool]
    langfuse_configured: bool
    langfuse_host: str


class SettingsUpdateRequest(BaseModel):
    default_model: str | None = None
    default_provider: str | None = None
    default_thinking_level: str | None = None
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


class ModelTestRequest(BaseModel):
    model: str
    provider: str = "gemini"


class ModelTestResponse(BaseModel):
    success: bool
    model: str
    latency_ms: int
    message: str
    error_type: str | None = None
