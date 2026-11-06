"""Pydantic schemas for Inbox and Ingestion APIs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InboxFileItem(BaseModel):
    filename: str
    size_bytes: int
    extension: str
    is_indexed: bool = False
    doc_id: Optional[str] = None


class InboxScanResponse(BaseModel):
    total_files: int
    unindexed_files: int
    files: List[InboxFileItem]
    skipped_duplicates: List[Dict[str, Any]] = Field(default_factory=list)


class InboxProcessRequest(BaseModel):
    force: bool = False
    move_archive: bool = False


class InboxProcessResponse(BaseModel):
    processed_count: int
    indexed_count: int
    skipped_count: int
    job_id: Optional[str] = None
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
    ingested_at: Optional[str] = None
    indexed_at: Optional[str] = None


class ArticleListResponse(BaseModel):
    total: int
    items: List[ArticleSummaryItem]


class InboxStatsResponse(BaseModel):
    total_articles: int
    indexed_articles: int
    total_creations: int
    storage_path: str
