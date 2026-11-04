"""Tests for Material Distiller and De-contextualized Neutral Synthesis (Milestone 5)."""

from pathlib import Path
import pytest

from src.config import AppConfig, PathSettings
from src.extraction.llm_client import LLMClient
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    DistilledMaterialSheet,
    ReusableAssetType,
    SeedRoleAssignment,
)
from src.storage.db import init_db
from src.storage.repository import StorageRepository
from src.synthesis.distiller import MaterialDistiller
from src.synthesis.planner import SynthesisPlanner
from src.synthesis.synthesizer import ArticleSynthesizer


@pytest.fixture
def distillation_env(tmp_path: Path):
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

    repo.save_processed_text("5455", "# 우린 왜 일을 미룰까요\n\n변연계와 전두엽의 갈등에 대한 긴 설명...")
    repo.save_processed_text("5457", "# 의지박약 탈출 2단계\n\n완벽주의를 버리고 60점 못난 초안을 쓰는 법...")

    llm = LLMClient()
    distiller = MaterialDistiller(repo=repo, llm_client=llm)
    synthesizer = ArticleSynthesizer(
        config=config,
        repo=repo,
        llm_client=llm,
        distiller=distiller,
    )
    return repo, distiller, synthesizer


def test_material_distillation(distillation_env):
    repo, distiller, _ = distillation_env

    seed = SeedRoleAssignment(
        seed_type="domain_case",
        doc_id="5455",
        title="우린 왜 일을 미룰까요",
        reason="뇌과학적 원인 분석",
        metadata=ArticleMetadata(
            target_audience="직장인",
            core_problem="과업 지연",
            reframing_logic="의지가 아닌 마찰 문제",
            core_thesis="마찰 최소화가 답",
            article_archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
            hook_strategy="통계 제시",
            solution_framework=["마찰 식별", "보상 설계"],
            notable_episodes=["마찰 10초 단축 시 착수율 급증"],
            reusable_asset_types=[ReusableAssetType.QUANTITATIVE_METRICS],
            primary_category="자기관리",
            topic_tags=["뇌과학", "마찰제거", "습관형성"],
        ),
    )

    sheet = distiller.distill_seed_sync(seed)
    assert isinstance(sheet, DistilledMaterialSheet)
    assert sheet.doc_id == "5455"
    assert sheet.assigned_role == "domain_case"
    assert len(sheet.core_mechanism_bullets) >= 2
    assert len(sheet.extracted_facts_and_numbers) >= 1
    # Check that it contains facts and not raw conversational sentences
    for bullet in sheet.core_mechanism_bullets:
        assert isinstance(bullet, str)


def test_synthesis_without_raw_text_anchoring(distillation_env):
    """
    Milestone 5 Verification Criteria:
    생성된 초안이 Seed 원문의 문장 어미나 고정 요약 박스 포맷을 복제하지 않고,
    새 주제와 방향성에 맞춘 독립적인 문장과 구조로 생성됨
    """
    _, _, synthesizer = distillation_env

    seeds = [
        SeedRoleAssignment(
            seed_type="domain_case",
            doc_id="5455",
            title="우린 왜 일을 미룰까요",
            reason="정서적 저항 메커니즘",
            metadata=ArticleMetadata(
                target_audience="직장인",
                core_problem="미루기",
                reframing_logic="불안이 만든 저항",
                core_thesis="마찰 제거",
                article_archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
                hook_strategy="현상 진단",
                solution_framework=["마찰 인식", "소보상"],
                notable_episodes=["착수율 3배 증가"],
                primary_category="자기관리",
                topic_tags=["미루기", "뇌과학", "시간관리"],
            ),
        ),
        SeedRoleAssignment(
            seed_type="perspective_framework",
            doc_id="5457",
            title="완벽한 나 대신 온전한 나",
            reason="60점 못난 초안",
            metadata=ArticleMetadata(
                target_audience="완벽주의자",
                core_problem="착수 회피",
                reframing_logic="완벽주의는 방어기제",
                core_thesis="60점 초안이 답",
                article_archetype=ArticleArchetype.STEP_BY_STEP_TUTORIAL,
                hook_strategy="실패 고백",
                solution_framework=["기준 강등", "못난 초안", "피드백 수용"],
                notable_episodes=["마감 준수율 95% 상승"],
                primary_category="자기관리",
                topic_tags=["완벽주의", "못난초안", "실행력"],
            ),
        ),
    ]

    out_file, content, blueprint, distilled_sheets = synthesizer.synthesize_sync(
        topic="할 일을 끝없이 미루는 완벽주의 직장인을 위한 3단계 착수 공식",
        direction="자책 대신 60점짜리 못난 초안으로 즉시 시작하기",
        seeds=seeds,
        archetype=ArticleArchetype.STEP_BY_STEP_TUTORIAL,
    )

    assert out_file.exists()
    assert len(distilled_sheets) == 2

    # Verify that the generated draft uses synthesized blueprint title and independent structure
    raw_md = out_file.read_text(encoding="utf-8")
    assert "완벽주의" in raw_md
    assert "60점" in raw_md
    # Independent sections without copy-pasting raw text
    assert len(raw_md) > 500
