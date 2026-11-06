"""Pydantic schemas for Draft Generation and Synthesis APIs."""

from typing import Any

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
    solution_framework: list[str] = Field(default_factory=list)
    notable_episodes: list[str] = Field(default_factory=list)
    topic_tags: list[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    assigned_role: str | None = None


class SeedSearchResponse(BaseModel):
    topic: str
    direction: str
    total_found: int
    candidates: list[SeedCandidateItem]


class BlueprintGenerateRequest(BaseModel):
    topic: str
    direction: str = ""
    target_archetype: str = "PRACTICAL_GUIDE"
    selected_seed_ids: list[str] = Field(default_factory=list)
    model: str | None = None


class BlueprintGenerateResponse(BaseModel):
    working_title: str
    core_thesis: str
    target_audience: str
    hook_strategy: str
    key_framework: list[str] = Field(default_factory=list)
    outline_sections: list[dict[str, Any]] = Field(default_factory=list)
    selected_seed_ids: list[str] = Field(default_factory=list)
    raw_blueprint: dict[str, Any] = Field(default_factory=dict)


class DraftSynthesizeRequest(BaseModel):
    topic: str
    direction: str = ""
    target_archetype: str = "PRACTICAL_GUIDE"
    selected_seed_ids: list[str] = Field(default_factory=list)
    blueprint: dict[str, Any] = Field(default_factory=dict)
    target_length: int = 2500
    model: str | None = None


class DraftSynthesizeResponse(BaseModel):
    title: str
    content: str
    char_count: int
    topic: str
    direction: str
    seed_doc_ids: list[str] = Field(default_factory=list)
    creation_id: str | None = None


class RandomInspirationRequest(BaseModel):
    preferred_category: str | None = None
    count: int = 3
    model: str | None = None


class RandomInspirationResponse(BaseModel):
    topic: str
    direction: str
    target_archetype: str = "PRACTICAL_GUIDE"
    concept_summary: str = ""
    selected_seeds: list[SeedCandidateItem] = Field(default_factory=list)


class VisualAssetResponseItem(BaseModel):
    doc_id: str
    doc_title: str
    asset_id: str
    page_no: int
    file_path: str
    image_url: str
    caption: str = ""
    width: int | None = None
    height: int | None = None


class SeedAssetsResponse(BaseModel):
    total: int
    assets: list[VisualAssetResponseItem] = Field(default_factory=list)


