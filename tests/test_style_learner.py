"""Tests for Milestone 7: Style Learner and Style Learning Loop."""

from pathlib import Path

import pytest

from src.config import AppConfig, PathSettings
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    ReusableAssetType,
    SeedRoleAssignment,
    UserStyleProfile,
)
from src.storage.db import init_db
from src.storage.repository import StorageRepository
from src.synthesis.style_learner import StyleLearner
from src.synthesis.synthesizer import ArticleSynthesizer


@pytest.fixture
def style_env(tmp_path: Path, mock_llm_client):
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
        )
    )
    config.ensure_directories()
    repo = StorageRepository(db_path=db_path, processed_dir=processed_dir)
    llm = mock_llm_client
    learner = StyleLearner(config=config, repo=repo, llm_client=llm)
    synthesizer = ArticleSynthesizer(config=config, repo=repo, llm_client=llm)
    return repo, learner, synthesizer, config


def test_style_learning_cycle(style_env):
    """
    Milestone 7 Verification Criteria:
    status='FINALIZED' 결과물 5개 이상 누적 시 Diff 기반 style_profile.json 생성 및 합성기 연동
    """
    repo, learner, synthesizer, config = style_env

    # 1. Initial state: 0 finalized creations -> learning candidates empty
    assert len(learner.get_finalized_candidates(min_count=5)) == 0
    assert learner.get_active_profile() is None

    # 2. Add 5 drafts and finalize them with user revisions
    for i in range(1, 6):
        cid = f"cr_test_{i:03d}"
        repo.save_draft_creation(
            creation_id=cid,
            topic=f"테스트 아티클 주제 {i}",
            direction="실무 중심",
            target_archetype="framework_checklist",
            seed_doc_ids=["5454", "5455"],
            blueprint_json='{"proposed_title": "가제"}',
            distilled_sheets_json='[]',
            ai_draft_text=f"# AI 초안 {i}\n\n이것은 AI가 작성한 다소 과장된 초안입니다.\n\n### 👀 바쁘다면 이거라도!\n1. 요약 박스",
            status="DRAFT",
        )
        # User finalizes it by deleting the box and refining tone
        user_edited = f"# 완성된 아티클 {i}\n\n사용자가 단문 위주로 군더더기를 제거하고 신뢰성 있게 퇴고한 글입니다."
        repo.update_creation_final(
            creation_id=cid,
            user_final_text=user_edited,
            custom_notes="요약 박스 삭제 및 단문 종결어미 통일",
            status="FINALIZED",
        )
        # Also save to my_corpus
        learner.save_finalized_article(creation_id=cid, title=f"완성본_{i}", content=user_edited)

    # Verify that my_corpus directory now contains saved markdown files
    corpus_files = list(learner.my_corpus_dir.glob("*.md"))
    assert len(corpus_files) == 5

    # 3. Check candidates: exactly 5 items available
    candidates = learner.get_finalized_candidates(min_count=5)
    assert len(candidates) == 5

    # 4. Extract style profile
    profile = learner.learn_style_sync(min_count=5)
    assert isinstance(profile, UserStyleProfile)
    assert profile.based_on_creation_count == 5
    assert len(profile.preferred_tone_and_endings) >= 1
    assert len(profile.forbidden_patterns) >= 1

    # 5. Verify persisted style_profile.json file
    assert learner.profile_path.exists()
    active = learner.get_active_profile()
    assert active is not None
    assert active.based_on_creation_count == 5

    # 6. Verify candidates are now marked as used (0 remaining for next cycle)
    remaining_candidates = learner.get_finalized_candidates(min_count=1)
    assert len(remaining_candidates) == 0

    # 7. Synthesizer with active style profile integration
    # Seed an indexed article
    repo.save_processed_text("5454", "# 본문\n내용")
    meta = ArticleMetadata(
        target_audience="독자",
        core_problem="문제",
        reframing_logic="전환",
        core_thesis="결론",
        article_archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
        hook_strategy="질문",
        solution_framework=["1단계", "2단계"],
        notable_episodes=["에피소드"],
        reusable_asset_types=[ReusableAssetType.QUANTITATIVE_METRICS],
        primary_category="업무스킬",
        topic_tags=["업무", "효율", "개선"],
    )
    seeds = [
        SeedRoleAssignment(
            seed_type="domain_case",
            doc_id="5454",
            title="테스트 문서",
            reason="테스트",
            metadata=meta,
        )
    ]

    out_file, content, blueprint, sheets = synthesizer.synthesize_sync(
        topic="스타일 프로필이 적용된 새 글",
        direction="간결하고 단정한 문체",
        seeds=seeds,
        style_profile=active,
    )

    assert out_file.exists()
    assert "style_profile_applied: true" in content
