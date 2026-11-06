"""Pydantic schemas for Style Learning and Persona Profile APIs."""

from typing import Any

from pydantic import BaseModel, Field


class StyleProfileResponse(BaseModel):
    persona_name: str = "Chief Business Essayist"
    tone_and_manner: list[str] = Field(default_factory=list)
    sentence_style: dict[str, Any] = Field(default_factory=dict)
    vocabulary_profile: dict[str, Any] = Field(default_factory=dict)
    storytelling_structures: list[str] = Field(default_factory=list)
    banned_patterns: list[str] = Field(default_factory=list)
    raw_profile: dict[str, Any] = Field(default_factory=dict)


class StyleUpdateRequest(BaseModel):
    profile_data: dict[str, Any]


class StyleLearnRequest(BaseModel):
    sample_texts: list[str] | None = None
    use_finalized_creations: bool = True
    min_finalized_count: int = 1
    force: bool = False
    window_size: int = 10


class StyleLearnResponse(BaseModel):
    success: bool
    learned_creations_count: int
    updated_profile: dict[str, Any] = Field(default_factory=dict)
    message: str
