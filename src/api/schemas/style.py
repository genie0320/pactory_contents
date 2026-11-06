"""Pydantic schemas for Style Learning and Persona Profile APIs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StyleProfileResponse(BaseModel):
    persona_name: str = "Chief Business Essayist"
    tone_and_manner: List[str] = Field(default_factory=list)
    sentence_style: Dict[str, Any] = Field(default_factory=dict)
    vocabulary_profile: Dict[str, Any] = Field(default_factory=dict)
    storytelling_structures: List[str] = Field(default_factory=list)
    banned_patterns: List[str] = Field(default_factory=list)
    raw_profile: Dict[str, Any] = Field(default_factory=dict)


class StyleUpdateRequest(BaseModel):
    profile_data: Dict[str, Any]


class StyleLearnRequest(BaseModel):
    sample_texts: Optional[List[str]] = None
    use_finalized_creations: bool = True
    min_finalized_count: int = 3


class StyleLearnResponse(BaseModel):
    success: bool
    learned_creations_count: int
    updated_profile: Dict[str, Any] = Field(default_factory=dict)
    message: str
