"""Pydantic schemas for Inbox and Ingestion APIs."""

from typing import Any

from pydantic import BaseModel, Field


class InboxFileItem(BaseModel):
    filename: str
    size_bytes: int
    extension: str
    is_indexed: bool = False
    doc_id: str | None = None


class InboxScanResponse(BaseModel):
    total_files: int
    unindexed_files: int
    files: list[InboxFileItem]
    skipped_duplicates: list[dict[str, Any]] = Field(default_factory=list)


class InboxProcessRequest(BaseModel):
    force: bool = False
    move_archive: bool = True


class InboxProcessResponse(BaseModel):
    processed_count: int
    indexed_count: int
    skipped_count: int
    job_id: str | None = None
    status: str = "COMPLETED"
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    current_doc_id: str = ""
    log_summary: str = ""
    started_at: str = ""
    updated_at: str = ""
    completed_at: str | None = None


class InboxUploadResponse(BaseModel):
    uploaded_count: int
    saved_files: list[str]
    message: str


class ArticleSummaryItem(BaseModel):
    doc_id: str
    title: str
    author: str = ""
    published_date: str = ""
    source_format: str = "markdown"
    char_count: int = 0
    image_count: int = 0
    status: str = "REGISTERED"
    primary_category: str | None = None
    article_archetype: str | None = None
    core_thesis: str | None = None
    reusable_asset_types: list[str] = Field(default_factory=list)
    target_audience: str | None = None
    core_problem: str | None = None
    reframing_logic: str | None = None
    hook_strategy: str | None = None
    solution_framework: list[str] = Field(default_factory=list)
    notable_episodes: list[str] = Field(default_factory=list)
    topic_tags: list[str] = Field(default_factory=list)
    ingested_at: str | None = None
    indexed_at: str | None = None


class ArticleListResponse(BaseModel):
    total: int
    items: list[ArticleSummaryItem]


class InboxStatsResponse(BaseModel):
    total_articles: int
    indexed_articles: int
    total_creations: int
    storage_path: str
