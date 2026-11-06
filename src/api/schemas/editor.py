"""Pydantic schemas for Studio Editor, Creations, and Proofreading APIs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreationSummaryItem(BaseModel):
    creation_id: str
    topic: str
    direction: str = ""
    target_archetype: str = "PRACTICAL_GUIDE"
    status: str = "DRAFT"
    created_at: str
    finalized_at: Optional[str] = None
    has_final: bool = False
    title: str = "제목 미정"
    seed_doc_ids: List[str] = Field(default_factory=list)


class CreationDetailResponse(BaseModel):
    creation_id: str
    topic: str
    direction: str = ""
    target_archetype: str = "PRACTICAL_GUIDE"
    ai_draft_text: str
    user_final_text: str = ""
    custom_notes: str = ""
    status: str = "DRAFT"
    seed_doc_ids: List[str] = Field(default_factory=list)
    created_at: str
    finalized_at: Optional[str] = None


class CreationSaveRequest(BaseModel):
    topic: str
    direction: str = ""
    target_archetype: str = "PRACTICAL_GUIDE"
    seed_doc_ids: List[str] = Field(default_factory=list)
    blueprint_json: str = "{}"
    distilled_sheets_json: str = "[]"
    ai_draft_text: str
    status: str = "DRAFT"


class CreationUpdateRequest(BaseModel):
    user_final_text: str
    custom_notes: str = ""
    status: str = "FINALIZED"


class ProofreadRequest(BaseModel):
    content: str
    platform: str = "general"
    mode: str = "report"
    custom_instruction: str = ""
    critique_feedback: str = ""
    metadata_context: str = ""


class ProofreadResponse(BaseModel):
    platform: str
    mode: str
    critique_report: str
    rewritten_text: Optional[str] = None
    hooking_score: int = 9
    balance_score: int = 9
    platform_score: int = 9
    suggested_title: str = "제목 미정"
