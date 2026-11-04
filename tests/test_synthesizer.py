"""Tests for SynthesisPlanner and ArticleSynthesizer (Milestone 4)."""

from pathlib import Path
import pytest

from src.config import AppConfig, PathSettings
from src.extraction.llm_client import LLMClient
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    ReusableAssetType,
    SeedRoleAssignment,
    SynthesisBlueprint,
)
from src.storage.db import init_db
from src.storage.repository import StorageRepository
from src.synthesis.planner import SynthesisPlanner
from src.synthesis.synthesizer import ArticleSynthesizer


@pytest.fixture
def synthesizer_env(tmp_path: Path):
    db_path = tmp_path / "index" / "catalog.db"
    processed_dir = tmp_path / "processed"
    outputs_dir = tmp_path / "outputs"
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
            outputs_dir=outputs_dir,
        )
    )
    config.ensure_directories()
    repo = StorageRepository(db_path=db_path, processed_dir=processed_dir)

    # Seed 1 text
    repo.save_processed_text("8194", "# AI 서비스 첫 판매기\n\n초기 활성 유저 0명의 실패에서 시작했습니다...")
    # Seed 2 text
    repo.save_processed_text("8195", "# 습관 형성 치트키\n\n의지가 아니라 마찰을 제거하는 3단계 시스템...")
    # Seed 3 text
    repo.save_processed_text("8204", "# 연말 프로모션 D-90 역산 기획\n\n체크리스트 표와 단계별 튜토리얼...")

    llm = LLMClient()
    planner = SynthesisPlanner(llm_client=llm)
    synthesizer = ArticleSynthesizer(
        config=config,
        repo=repo,
        llm_client=llm,
        planner=planner,
    )
    return repo, synthesizer, config


def test_blueprint_planner():
    llm = LLMClient()
    planner = SynthesisPlanner(llm_client=llm)

    seeds = [
        SeedRoleAssignment(
            seed_type="domain_case",
            doc_id="8194",
            title="AI 서비스 첫 판매기",
            reason="초기 유입 0건 실패담",
            metadata=ArticleMetadata(
                target_audience="주니어 실무자",
                core_problem="도구 방치",
                reframing_logic="도구 문제가 아닌 마찰 문제",
                core_thesis="마찰 해소가 핵심",
                article_archetype=ArticleArchetype.TRIAL_AND_ERROR_RETRO,
                hook_strategy="실패 고백",
                solution_framework=["마찰 식별", "1초 버튼"],
                notable_episodes=["사용자 0명 극복"],
                reusable_asset_types=[ReusableAssetType.FAILURE_EPISODE],
                primary_category="서비스기획/AI",
                topic_tags=["AI", "자동화", "도입"],
            ),
        ),
    ]

    blueprint = planner.plan_blueprint_sync(
        topic="비개발자 실무자의 AI 자동화",
        direction="운영과 마찰 최소화",
        seeds=seeds,
        archetype=ArticleArchetype.TRIAL_AND_ERROR_RETRO,
    )

    assert isinstance(blueprint, SynthesisBlueprint)
    assert len(blueprint.proposed_title) > 0
    assert len(blueprint.section_outline) >= 3


def test_draft_synthesis_output_creation(synthesizer_env):
    """
    Milestone 4 Verification Criteria:
    상호 보완적인 Seed 2~3편이 선별되고, 구조화된 초안 .md 파일이 data/outputs/에 생성됨
    """
    _, synthesizer, config = synthesizer_env

    seeds = [
        SeedRoleAssignment(
            seed_type="domain_case",
            doc_id="8194",
            title="AI 서비스 첫 판매기",
            reason="초기 0명 실패담",
            metadata=ArticleMetadata(
                target_audience="주니어 기획자",
                core_problem="도구 방치",
                reframing_logic="도구 문제가 아닌 마찰의 문제",
                core_thesis="마찰 해소가 핵심",
                article_archetype=ArticleArchetype.TRIAL_AND_ERROR_RETRO,
                hook_strategy="실패 수치 공개",
                solution_framework=["마찰 식별", "1초 버튼"],
                notable_episodes=["0명에서 전원 전환"],
                reusable_asset_types=[ReusableAssetType.FAILURE_EPISODE],
                primary_category="서비스기획/AI",
                topic_tags=["AI자동화", "실무도입", "업무효율"],
            ),
        ),
        SeedRoleAssignment(
            seed_type="perspective_framework",
            doc_id="8195",
            title="습관 형성 치트키",
            reason="마찰 제거 3단계 공식",
            metadata=ArticleMetadata(
                target_audience="직장인",
                core_problem="작심삼일",
                reframing_logic="의지가 아니라 마찰의 문제다",
                core_thesis="환경 통제가 답이다",
                article_archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
                hook_strategy="통계 제시",
                solution_framework=["물리적 마찰 제거", "1초 장치", "피드백 루프"],
                notable_episodes=["월 4권 완독"],
                reusable_asset_types=[ReusableAssetType.CHECKLIST_TABLE],
                primary_category="자기관리",
                topic_tags=["마찰제거", "루틴", "습관설계"],
            ),
        ),
    ]

    out_file, content, blueprint, distilled_sheets = synthesizer.synthesize_sync(
        topic="비개발자 실무자의 사내 AI 자동화 도입기",
        direction="도구 자랑이 아니라 팀원들이 실제로 쓰게 만드는 운영과 마찰 제거",
        seeds=seeds,
        archetype=ArticleArchetype.TRIAL_AND_ERROR_RETRO,
    )

    # 1. Output file exists
    assert out_file.exists()
    assert out_file.suffix == ".md"
    assert len(distilled_sheets) == 2

    # 2. YAML frontmatter check
    raw_text = out_file.read_text(encoding="utf-8")
    assert raw_text.startswith("---")
    assert "seeds_used" in raw_text
    assert "8194" in raw_text
    assert "8195" in raw_text
    assert "synthesized_reframing" in raw_text

    # 3. Content check: Guardrail checklist
    assert len(raw_text) > 300
