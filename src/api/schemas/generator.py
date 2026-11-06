"""Pydantic schemas for Draft Generation and Synthesis APIs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SeedSearchRequest(BaseModel):
    topic: str
    direction: str = ""
    limit: int = 10
    threshold: float = 0.0


class SeedCandidateItem(BaseModel):
    doc_id: str
    title: str
    archetype: str = "PRACTICAL_GUIDE"
    target_audience: str = ""
    core_thesis: str = ""
    solution_framework: List[str] = Field(default_factory=list)
    notable_episodes: List[str] = Field(default_factory=list)
    topic_tags: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    assigned_role: Optional[str] = None


class SeedSearchResponse(BaseModel):
    topic: str
    direction: str
    total_found: int
    candidates: List[SeedCandidateItem]


class BlueprintGenerateRequest(BaseModel):
    topic: str
    direction: str = ""
    target_archetype: str = "PRACTICAL_GUIDE"
    selected_seed_ids: List[str] = Field(default_factory=list)


class BlueprintGenerateResponse(BaseModel):
    working_title: str
    core_thesis: str
    target_audience: str
    hook_strategy: str
    key_framework: List[str] = Field(default_factory=list)
    outline_sections: List[Dict[str, Any]] = Field(default_factory=list)
    selected_seed_ids: List[str] = Field(default_factory=list)
    raw_blueprint: Dict[str, Any] = Field(default_factory=dict)


class DraftSynthesizeRequest(BaseModel):
    topic: str
    direction: str = ""
    target_archetype: str = "PRACTICAL_GUIDE"
    selected_seed_ids: List[str] = Field(default_factory=list)
    blueprint: Dict[str, Any] = Field(default_factory=dict)
    target_length: int = 2500


class DraftSynthesizeResponse(BaseModel):
    title: str
    content: str
    char_count: int
    topic: str
    direction: str
    seed_doc_ids: List[str] = Field(default_factory=list)
    creation_id: Optional[str] = None
