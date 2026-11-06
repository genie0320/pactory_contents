"""Inbox and Ingestion API router."""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.auth import verify_auth
from src.api.schemas.inbox import (
    ArticleListResponse,
    ArticleSummaryItem,
    InboxFileItem,
    InboxProcessRequest,
    InboxProcessResponse,
    InboxScanResponse,
    InboxStatsResponse,
)
from src.config import load_config
from src.ingestion.scanner import IngestionScanner
from src.storage.repository import StorageRepository

router = APIRouter(prefix="/inbox", tags=["Inbox & Ingestion"], dependencies=[Depends(verify_auth)])


@router.get("/scan", response_model=InboxScanResponse)
async def scan_inbox():
    """Scan inbox folder and return status of unindexed vs existing files."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    scanner = IngestionScanner(config=config, repo=repo)

    inbox_dir = config.paths.inbox_dir
    inbox_dir.mkdir(parents=True, exist_ok=True)

    supported_extensions = {".pdf", ".md", ".txt"}
    files: List[InboxFileItem] = []
    unindexed_count = 0

    for p in sorted(inbox_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in supported_extensions:
            file_hash = scanner.compute_sha256(p)
            doc_id, _ = scanner.parse_filename(p.name)
            existing = repo.get_article_by_hash(file_hash)
            if not existing and doc_id:
                existing = repo.get_article(doc_id)

            is_indexed = existing is not None and existing.status == "INDEXED"
            matched_doc_id = existing.doc_id if existing else doc_id

            if not is_indexed:
                unindexed_count += 1

            files.append(
                InboxFileItem(
                    filename=p.name,
                    size_bytes=p.stat().st_size,
                    extension=p.suffix.lower(),
                    is_indexed=is_indexed,
                    doc_id=matched_doc_id,
                )
            )

    return InboxScanResponse(
        total_files=len(files),
        unindexed_files=unindexed_count,
        files=files,
        skipped_duplicates=[],
    )


@router.post("/process", response_model=InboxProcessResponse)
async def process_inbox(req: InboxProcessRequest):
    """Run ingestion scanning and metadata indexing on inbox files."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    scanner = IngestionScanner(config=config, repo=repo)

    processed_records = scanner.scan_inbox(
        force=req.force,
        move_archive=req.move_archive,
    )

    new_count = len(scanner.last_newly_processed)
    skip_count = len(scanner.last_skipped_duplicates)

    # Automatically extract metadata for REGISTERED articles if LLM key is available
    from src.extraction.batch_extractor import BatchExtractor
    from src.extraction.llm_client import LLMClient

    llm = LLMClient()
    indexed_count = 0
    if llm.api_key:
        extractor = BatchExtractor(config=config, repo=repo, llm_client=llm)
        indexed_count = extractor.process_unindexed(batch_size=10)

    return InboxProcessResponse(
        processed_count=len(processed_records),
        indexed_count=indexed_count,
        skipped_count=skip_count,
        message=f"처리 완료: 신규 색인 {new_count}건, 중복 건너뜀 {skip_count}건, 메타데이터 추출 {indexed_count}건",
    )


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
):
    """List indexed articles from the catalog database."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    articles = repo.list_articles(status=status, limit=limit)

    items = [
        ArticleSummaryItem(
            doc_id=a.doc_id,
            title=a.title,
            author=a.author,
            published_date=a.published_date,
            source_format=a.source_format,
            char_count=a.char_count,
            image_count=a.image_count,
            status=a.status,
            ingested_at=a.ingested_at.isoformat() if a.ingested_at else None,
            indexed_at=a.indexed_at.isoformat() if a.indexed_at else None,
        )
        for a in articles
    ]

    return ArticleListResponse(total=len(items), items=items)


@router.get("/stats", response_model=InboxStatsResponse)
async def get_inbox_stats():
    """Retrieve catalog and storage statistics."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    all_articles = repo.list_articles(limit=1000)
    indexed_count = sum(1 for a in all_articles if a.status == "INDEXED")
    creations = repo.list_creations(limit=1000)

    return InboxStatsResponse(
        total_articles=len(all_articles),
        indexed_articles=indexed_count,
        total_creations=len(creations),
        storage_path=str(config.paths.data_dir.resolve()),
    )
