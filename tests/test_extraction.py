"""Tests for Asynchronous Metadata Batch Extractor and Fault-Tolerant Checkpointing (Milestone 3)."""

from pathlib import Path

import pytest

from src.config import AppConfig, ExtractionSettings, PathSettings
from src.extraction.batch_extractor import BatchMetadataExtractor
from src.models import (
    ArticleRecord,
    ArticleStatus,
)
from src.storage.db import init_db
from src.storage.repository import StorageRepository


@pytest.fixture
def extraction_env(tmp_path: Path, mock_llm_client):
    db_path = tmp_path / "index" / "catalog.db"
    processed_dir = tmp_path / "processed"
    init_db(db_path)

    config = AppConfig(
        paths=PathSettings(
            data_dir=tmp_path,
            inbox_dir=tmp_path / "inbox",
            archive_dir=tmp_path / "archive",
            processed_dir=processed_dir,
            texts_dir=processed_dir / "texts",
            metadata_dir=processed_dir / "metadata",
            assets_dir=processed_dir / "assets",
            index_dir=tmp_path / "index",
            db_path=db_path,
            outputs_dir=tmp_path / "outputs",
        ),
        extraction=ExtractionSettings(concurrency=3),
    )
    config.ensure_directories()
    repo = StorageRepository(db_path=db_path, processed_dir=processed_dir)
    llm_client = mock_llm_client
    extractor = BatchMetadataExtractor(
        config=config,
        repo=repo,
        llm_client=llm_client,
        concurrency=3,
    )
    return repo, extractor, config


def test_structured_metadata_extraction(extraction_env):
    repo, extractor, _ = extraction_env

    # Setup 1 ingested article
    doc_id = "8301"
    repo.save_processed_text(
        doc_id=doc_id,
        content="# 비개발자 실무자의 AI 자동화 도입기\n\n업무에 AI를 도입하면서 겪은 시행착오...",
    )
    article = ArticleRecord(
        doc_id=doc_id,
        title="비개발자 실무자의 AI 자동화 도입기",
        source_format="md",
        original_path=f"archive/{doc_id}.md",
        processed_text_path=f"processed/texts/{doc_id}.md",
        content_hash="hash8301",
        char_count=500,
        status=ArticleStatus.INGESTED,
    )
    repo.upsert_article(article)

    # Run extraction
    processed = extractor.run_sync()
    assert doc_id in processed

    # Verify status changed to INDEXED
    updated = repo.get_article(doc_id)
    assert updated.status == ArticleStatus.INDEXED
    assert updated.indexed_at is not None

    # Verify metadata saved
    meta = repo.get_article_metadata(doc_id)
    assert meta is not None
    assert isinstance(meta.reframing_logic, str)
    assert len(meta.solution_framework) >= 2


def test_fault_tolerant_checkpointing_resumption(extraction_env):
    """
    Milestone 3 Verification Criteria:
    추출 중 강제 중단 후 재실행 시 이미 INDEXED 상태인 문서는 건너뛰고
    미처리 문서만 정확히 이어받아 완료함
    """
    repo, extractor, _ = extraction_env

    # Register 6 ingested articles
    doc_ids = [f"840{i}" for i in range(1, 7)]
    for did in doc_ids:
        repo.save_processed_text(
            doc_id=did,
            content=f"# 아티클 {did}\n\n이것은 {did}번 본문 텍스트입니다. 다양한 노하우와 프레임워크가 담겨 있습니다.",
        )
        article = ArticleRecord(
            doc_id=did,
            title=f"아티클 제목 {did}",
            source_format="md",
            original_path=f"archive/{did}.md",
            processed_text_path=f"processed/texts/{did}.md",
            content_hash=f"hash_{did}",
            char_count=600,
            status=ArticleStatus.INGESTED,
        )
        repo.upsert_article(article)

    # Initial pending count: 6
    pending_before = extractor.get_pending_articles()
    assert len(pending_before) == 6

    # 1. Partial execution (simulating interruption after 3 items)
    first_batch_ids = extractor.run_sync(max_items=3)
    assert len(first_batch_ids) == 3

    # Check state after interruption
    for did in first_batch_ids:
        art = repo.get_article(did)
        assert art.status == ArticleStatus.INDEXED
        assert (repo.metadata_dir / f"{did}.json").exists()

    # Verify checkpoint: only remaining 3 are pending
    pending_mid = extractor.get_pending_articles()
    assert len(pending_mid) == 3
    remaining_ids = {a.doc_id for a in pending_mid}
    assert remaining_ids.isdisjoint(set(first_batch_ids))

    # 2. Resume execution (re-running without arguments)
    resumed_batch_ids = extractor.run_sync()
    assert len(resumed_batch_ids) == 3
    assert set(resumed_batch_ids) == remaining_ids

    # 3. Final verification: all 6 articles are now INDEXED, pending is 0
    pending_after = extractor.get_pending_articles()
    assert len(pending_after) == 0

    all_articles = repo.list_articles()
    for art in all_articles:
        assert art.status == ArticleStatus.INDEXED
