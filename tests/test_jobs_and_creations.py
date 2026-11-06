"""Tests for Milestone 6: Job logging (pipeline_jobs) and My Creation DB (drafts_and_creations)."""

from pathlib import Path

import pytest

from src.extraction.batch_extractor import BatchMetadataExtractor
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    ArticleRecord,
    ArticleStatus,
    ReusableAssetType,
    SeedRoleAssignment,
)
from src.storage.db import init_db
from src.storage.repository import StorageRepository
from src.synthesis.synthesizer import ArticleSynthesizer


@pytest.fixture
def repo(tmp_path: Path) -> StorageRepository:
    db_path = tmp_path / "test_catalog.db"
    processed_dir = tmp_path / "processed"
    init_db(db_path)
    return StorageRepository(db_path=db_path, processed_dir=processed_dir)


def test_pipeline_job_lifecycle(repo: StorageRepository):
    """Verify pipeline_jobs creation, incremental progress updates, and completion."""
    job_id = "test_extract_001"
    repo.create_job(job_id=job_id, job_type="METADATA_EXTRACTION", total_items=5)

    # Initial state
    job = repo.get_job(job_id)
    assert job is not None
    assert job["job_id"] == job_id
    assert job["job_type"] == "METADATA_EXTRACTION"
    assert job["status"] == "RUNNING"
    assert job["total_items"] == 5
    assert job["processed_items"] == 0
    assert job["failed_items"] == 0

    # Intermediate progress updates (real-time tracking)
    repo.update_job_progress(
        job_id=job_id,
        processed_delta=1,
        current_doc_id="doc_101",
        log_summary="Indexed doc_101 successfully",
    )
    job = repo.get_job(job_id)
    assert job["processed_items"] == 1
    assert job["current_doc_id"] == "doc_101"
    assert "doc_101" in job["log_summary"]
    assert job["status"] == "RUNNING"

    repo.update_job_progress(
        job_id=job_id,
        processed_delta=2,
        failed_delta=1,
        current_doc_id="doc_104",
        log_summary="Processed batch up to doc_104",
    )
    job = repo.get_job(job_id)
    assert job["processed_items"] == 3
    assert job["failed_items"] == 1
    assert job["current_doc_id"] == "doc_104"

    # Completion
    repo.complete_job(job_id=job_id, status="COMPLETED", log_summary="All items finished")
    job = repo.get_job(job_id)
    assert job["status"] == "COMPLETED"
    assert job["completed_at"] is not None
    assert job["log_summary"] == "All items finished"

    # List jobs
    jobs = repo.list_jobs(limit=10)
    assert len(jobs) >= 1
    assert jobs[0]["job_id"] == job_id


def test_drafts_and_creations_workflow(repo: StorageRepository):
    """Verify saving draft, listing drafts, updating to finalized, and query for learning."""
    creation_id = "cr_test_20261104"
    repo.save_draft_creation(
        creation_id=creation_id,
        topic="테스트 주제",
        direction="테스트 방향성",
        target_archetype="framework_tutorial",
        seed_doc_ids=["5454", "5455"],
        blueprint_json='{"proposed_title": "테스트 제목"}',
        distilled_sheets_json='[{"doc_id": "5454"}]',
        ai_draft_text="# 테스트 제목\n\nAI가 작성한 원본 초안입니다.",
        status="DRAFT",
    )

    creation = repo.get_creation(creation_id)
    assert creation is not None
    assert creation["topic"] == "테스트 주제"
    assert creation["status"] == "DRAFT"
    assert creation["user_final_text"] == ""
    assert creation["used_for_style_learning"] == 0
    assert creation["seed_doc_ids"] == ["5454", "5455"]

    # Update to finalized
    user_edited_text = "# 테스트 제목 (수정됨)\n\n사용자가 직접 다듬은 최종본 문장입니다."
    repo.update_creation_final(
        creation_id=creation_id,
        user_final_text=user_edited_text,
        custom_notes="종결어미 수정 및 서두 요약 삭제",
        status="FINALIZED",
    )

    finalized = repo.get_creation(creation_id)
    assert finalized["status"] == "FINALIZED"
    assert finalized["user_final_text"] == user_edited_text
    assert finalized["custom_notes"] == "종결어미 수정 및 서두 요약 삭제"
    assert finalized["finalized_at"] is not None

    # Check learning queries
    # Less than 5 finalized items should return empty list
    ready_for_learning = repo.get_finalized_creations_for_learning(min_count=5)
    assert len(ready_for_learning) == 0

    # When min_count=1, it should be retrieved
    single_learning = repo.get_finalized_creations_for_learning(min_count=1)
    assert len(single_learning) == 1
    assert single_learning[0]["creation_id"] == creation_id

    # Mark as used for style learning
    repo.mark_creations_used_for_style([creation_id])
    assert repo.get_creation(creation_id)["used_for_style_learning"] == 1
    assert len(repo.get_finalized_creations_for_learning(min_count=1)) == 0


def test_batch_extractor_job_tracking(repo: StorageRepository, mock_llm_client):
    """Verify that BatchMetadataExtractor creates and updates pipeline_jobs during execution."""
    # Seed 2 articles
    article1 = ArticleRecord(
        doc_id="job_test_1",
        title="테스트 문서 1",
        source_format="md",
        original_path="archive/job_test_1.md",
        processed_text_path="processed/texts/job_test_1.md",
        content_hash="hash_1",
        char_count=100,
        status=ArticleStatus.INGESTED,
    )
    article2 = ArticleRecord(
        doc_id="job_test_2",
        title="테스트 문서 2",
        source_format="md",
        original_path="archive/job_test_2.md",
        processed_text_path="processed/texts/job_test_2.md",
        content_hash="hash_2",
        char_count=120,
        status=ArticleStatus.INGESTED,
    )
    repo.upsert_article(article1)
    repo.upsert_article(article2)
    repo.save_processed_text("job_test_1", "# 1\n이것은 첫번째 테스트 내용입니다.")
    repo.save_processed_text("job_test_2", "# 2\n이것은 두번째 테스트 내용입니다.")

    extractor = BatchMetadataExtractor(repo=repo, llm_client=mock_llm_client)
    job_id = "job_batch_extract_run"
    extracted = extractor.run_sync(doc_ids=["job_test_1", "job_test_2"], job_id=job_id)

    assert len(extracted) == 2
    job = repo.get_job(job_id)
    assert job is not None
    assert job["status"] == "COMPLETED"
    assert job["total_items"] == 2
    assert job["processed_items"] == 2
    assert job["failed_items"] == 0


def test_synthesizer_job_and_creation_recording(repo: StorageRepository, mock_llm_client):
    """Verify that synthesizer creates drafts_and_creations record and logs pipeline job."""
    # Seed an article for distillation
    article = ArticleRecord(
        doc_id="seed_synth_1",
        title="조직 문제 해결",
        source_format="md",
        original_path="archive/seed_synth_1.md",
        processed_text_path="processed/texts/seed_synth_1.md",
        content_hash="hash_seed_1",
        char_count=150,
        status=ArticleStatus.INDEXED,
    )
    repo.upsert_article(article)
    repo.save_processed_text(
        "seed_synth_1",
        "# 조직 문제\n\n회의를 줄이기 위해 문서화 도입 -> 처리 속도 3배 증가.",
    )

    metadata = ArticleMetadata(
        target_audience="팀 리더",
        core_problem="비효율적 회의",
        reframing_logic="구두 회의보다 비동기 문서화가 효율적",
        core_thesis="비동기 문서 기반 의사결정",
        article_archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
        hook_strategy="실화 기반 에피소드",
        solution_framework=["문서화 규칙 수립", "사전 검토 프로세스"],
        notable_episodes=["회의 시간 70% 단축 사례"],
        reusable_asset_types=[ReusableAssetType.QUANTITATIVE_METRICS],
        primary_category="업무스킬",
        topic_tags=["업무효율", "회의단축", "문서화"],
    )

    seeds = [
        SeedRoleAssignment(
            doc_id="seed_synth_1",
            title="조직 문제 해결",
            seed_type="domain_case",
            reason="Core framework provider",
            metadata=metadata,
        )
    ]

    synthesizer = ArticleSynthesizer(repo=repo, llm_client=mock_llm_client)
    out_file, content, blueprint, sheets = synthesizer.synthesize_sync(
        topic="비개발자의 자동화 도입",
        direction="실무 신뢰 장치 중심",
        seeds=seeds,
        archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
    )

    assert out_file.exists()
    assert len(content) > 100

    # Check drafts_and_creations table
    creations = repo.list_creations()
    assert len(creations) >= 1
    latest = creations[0]
    assert latest["topic"] == "비개발자의 자동화 도입"
    assert latest["status"] == "DRAFT"
    assert "seed_synth_1" in latest["seed_doc_ids"]

    # Check pipeline_jobs table for synthesis job
    jobs = [j for j in repo.list_jobs() if j["job_type"] == "DRAFT_SYNTHESIS"]
    assert len(jobs) >= 1
    assert jobs[0]["status"] == "COMPLETED"
    assert jobs[0]["processed_items"] == 1
