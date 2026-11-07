"""Inbox and Ingestion API router."""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status

from src.api.auth import verify_auth
from src.api.dependencies import ConfigDep, RepoDep, build_article_detail
from src.api.schemas.inbox import (
    ArticleListResponse,
    ArticleSummaryItem,
    InboxFileItem,
    InboxProcessRequest,
    InboxProcessResponse,
    InboxScanResponse,
    InboxStatsResponse,
    InboxUploadResponse,
    JobStatusResponse,
)
from src.config import load_config
from src.ingestion.scanner import IngestionScanner
from src.storage.repository import StorageRepository

router = APIRouter(prefix="/inbox", tags=["Inbox & Ingestion"], dependencies=[Depends(verify_auth)])


async def _run_inbox_pipeline_task(
    job_id: str,
    force: bool,
    move_archive: bool,
):
    """Background worker for inbox file scanning, ingestion, and metadata extraction."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
    scanner = IngestionScanner(config=config, repo=repo)

    try:
        # 1. Ingestion Scan (Extract text, move to archive if move_archive=True)
        processed_records = scanner.scan_inbox(
            force=force,
            move_archive=move_archive,
            job_id=job_id,
        )
        new_count = len(scanner.last_newly_processed)
        skip_count = len(scanner.last_skipped_duplicates)

        repo.update_job_progress(
            job_id=job_id,
            total_items=new_count,
            processed_items=0,
            log_summary=f"문서 파싱 완료 (신규 {new_count}건, 중복 {skip_count}건). 메타데이터 추출 준비 중...",
        )

        # 2. Asynchronous Metadata Extraction
        if new_count > 0:
            from src.extraction.batch_extractor import BatchMetadataExtractor
            from src.extraction.llm_client import LLMClient

            llm = LLMClient(repo=repo)
            extractor = BatchMetadataExtractor(config=config, repo=repo, llm_client=llm)

            def on_progress(p: int, t: int, msg: str):
                repo.update_job_progress(
                    job_id=job_id,
                    processed_items=p,
                    total_items=t,
                    log_summary=msg,
                )

            await extractor.extract_all(
                force=force,
                progress_callback=on_progress,
                job_id=job_id,
                target_doc_ids=[r.doc_id for r in processed_records if r.doc_id in scanner.last_newly_processed],
            )

        repo.complete_job(
            job_id=job_id,
            log_summary=f"색인 및 메타데이터 추출 완료 (신규 처리 {new_count}건, 중복 건너뜀 {skip_count}건).",
        )
    except Exception as exc:
        repo.update_job_progress(
            job_id=job_id,
            status="FAILED",
            log_summary=f"파이프라인 실행 중 오류 발생: {exc}",
        )


@router.get("/scan", response_model=InboxScanResponse)
async def scan_inbox(repo: RepoDep, config: ConfigDep):
    """Scan inbox folder and return status of unindexed vs existing files."""
    scanner = IngestionScanner(config=config, repo=repo)

    inbox_dir = config.paths.inbox_dir
    inbox_dir.mkdir(parents=True, exist_ok=True)

    supported_extensions = {".pdf", ".md", ".txt"}
    files: list[InboxFileItem] = []
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


@router.post("/process", response_model=InboxProcessResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_inbox(
    req: InboxProcessRequest,
    background_tasks: BackgroundTasks,
    repo: RepoDep,
):
    """Run ingestion scanning and metadata indexing asynchronously via Job queue (202 Accepted)."""
    job_id = f"job_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    repo.create_job(job_id=job_id, job_type="INBOX_PIPELINE", total_items=0)

    background_tasks.add_task(
        _run_inbox_pipeline_task,
        job_id=job_id,
        force=req.force,
        move_archive=req.move_archive,
    )

    return InboxProcessResponse(
        processed_count=0,
        indexed_count=0,
        skipped_count=0,
        job_id=job_id,
        status="RUNNING",
        message="색인 작업이 백그라운드 큐에 등록되어 처리를 시작했습니다.",
    )


@router.get("/jobs/active", response_model=JobStatusResponse | None)
async def get_active_inbox_job(repo: RepoDep):
    """Retrieve the latest running inbox pipeline job if any."""
    jobs = repo.list_jobs(limit=10)
    for j in jobs:
        if j.get("status") == "RUNNING" and j.get("job_type") in ("INBOX_PIPELINE", "INGESTION", "METADATA_EXTRACTION"):
            return JobStatusResponse(**j)
    return None


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_inbox_job_status(job_id: str, repo: RepoDep):
    """Check progress and log summary of a specific pipeline job."""
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JobStatusResponse(**job)


@router.post("/upload", response_model=InboxUploadResponse)
async def upload_inbox_files(config: ConfigDep, files: list[UploadFile] = File(...)):
    """Upload documents directly into data/inbox folder for ingestion."""
    if not files:
        raise HTTPException(status_code=400, detail="업로드할 파일이 없습니다.")

    inbox_dir = config.paths.inbox_dir
    inbox_dir.mkdir(parents=True, exist_ok=True)

    allowed_extensions = {".pdf", ".docx", ".txt", ".md"}
    saved_files = []

    for f in files:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in allowed_extensions:
            continue

        dest_path = inbox_dir / f.filename
        content = await f.read()
        dest_path.write_bytes(content)
        saved_files.append(f.filename)

    if not saved_files:
        raise HTTPException(
            status_code=400,
            detail="지원되는 형식(.pdf, .docx, .txt, .md)의 유효한 파일이 없습니다.",
        )

    return InboxUploadResponse(
        uploaded_count=len(saved_files),
        saved_files=saved_files,
        message=f"{len(saved_files)}개 문서가 inbox에 정상적으로 업로드되었습니다.",
    )


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    repo: RepoDep,
    limit: int = Query(500, ge=1, le=1000),
    status: str | None = Query(None),
):
    """List indexed articles from the catalog database with metadata."""
    articles = repo.list_articles(status=status, limit=limit)

    items = []
    for a in articles:
        meta = repo.get_article_metadata(a.doc_id)
        archetype_val = None
        reusable_assets = []
        if meta:
            archetype_val = (
                meta.article_archetype.value
                if hasattr(meta.article_archetype, "value")
                else str(meta.article_archetype)
            )
            reusable_assets = [
                (t.value if hasattr(t, "value") else str(t))
                for t in (meta.reusable_asset_types or [])
            ]

        items.append(
            ArticleSummaryItem(
                doc_id=a.doc_id,
                title=a.title,
                author=a.author,
                published_date=a.published_date,
                source_format=a.source_format,
                char_count=a.char_count,
                image_count=a.image_count,
                status=a.status.value if hasattr(a.status, "value") else str(a.status),
                primary_category=meta.primary_category if meta else None,
                article_archetype=archetype_val,
                core_thesis=meta.core_thesis if meta else None,
                reusable_asset_types=reusable_assets,
                target_audience=meta.target_audience if meta else None,
                core_problem=meta.core_problem if meta else None,
                reframing_logic=meta.reframing_logic if meta else None,
                hook_strategy=meta.hook_strategy if meta else None,
                solution_framework=meta.solution_framework if meta else [],
                notable_episodes=meta.notable_episodes if meta else [],
                topic_tags=meta.topic_tags if meta else [],
                ingested_at=a.ingested_at.isoformat() if hasattr(a.ingested_at, "isoformat") else (str(a.ingested_at) if a.ingested_at else None),
                indexed_at=a.indexed_at.isoformat() if hasattr(a.indexed_at, "isoformat") else (str(a.indexed_at) if a.indexed_at else None),
            )
        )

    return ArticleListResponse(total=len(items), items=items)


@router.get("/articles/{doc_id}")
async def get_article_detail(doc_id: str, repo: RepoDep):
    """Retrieve complete metadata, visual assets, and text preview for a single article."""
    return build_article_detail(repo, doc_id)


@router.get("/stats", response_model=InboxStatsResponse)
async def get_inbox_stats(repo: RepoDep, config: ConfigDep):
    """Retrieve catalog and storage statistics."""
    all_articles = repo.list_articles(limit=1000)
    indexed_count = sum(1 for a in all_articles if a.status == "INDEXED")
    creations = repo.list_creations(limit=1000)

    return InboxStatsResponse(
        total_articles=len(all_articles),
        indexed_articles=indexed_count,
        total_creations=len(creations),
        storage_path=str(config.paths.data_dir.resolve()),
    )
