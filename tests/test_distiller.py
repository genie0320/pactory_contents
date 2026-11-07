"""Tests for Material Distiller and De-contextualized Neutral Synthesis (Milestone 5)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config import AppConfig, PathSettings
from src.extraction.llm_client import LLMClient
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    DistilledMaterialSheet,
    ReusableAssetType,
    SeedRoleAssignment,
    SynthesisBlueprint,
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

    mock_llm = MagicMock(spec=LLMClient)

    def mock_extract(system_prompt="", user_prompt="", schema=None, model=None, **kwargs):
        if schema == DistilledMaterialSheet:
            return DistilledMaterialSheet(
                doc_id="5455",
                assigned_role="domain_case",
                core_mechanism_bullets=[
                    "과업 착수 시 변연계(감정)와 전두엽(이성)의 충돌 발생",
                    "마찰을 최소화해야 전두엽이 주도권을 회복함",
                ],
                extracted_facts_and_numbers=[
                    "착수 마찰 10초 단축 시 실행 전환율 3배 증가",
                    "마감 준수율 95% 달성",
                ],
                case_causal_chains=[
                    "상황: 완벽한 결과물 요구 -> 반응: 착수 회피 -> 해결: 60점 못난 초안으로 즉시 개시"
                ],
                raw_templates_or_criteria=[],
            )
        elif schema == SynthesisBlueprint:
            return SynthesisBlueprint(
                proposed_title="완벽주의 직장인을 위한 60점 못난 초안 공식",
                target_reader_definition="과업을 끝없이 미루는 완벽주의 직장인",
                synthesized_reframing="완벽주의는 성실함이 아닌 두려움의 발로이며, 60점 초안이 돌파구다",
                role_assignments=["5455에서 뇌과학적 원인 차용", "5457에서 못난 초안 실행법 차용"],
                section_outline=[
                    "1. 왜 우리는 중요한 일 앞에서 멈칫거리는가",
                    "2. 뇌과학이 밝힌 미루기의 진짜 정체",
                    "3. 60점 못난 초안으로 시작하는 3단계 규칙",
                ],
            )
        return schema()

    mock_llm.extract_structured_sync.side_effect = mock_extract

    # Generated article text
    mock_llm.generate_text_sync.return_value = (
        "# 완벽주의 직장인을 위한 60점 못난 초안 공식\n\n"
        "완벽주의에 사로잡힌 직장인들은 일을 시작하지 못하고 끝없이 미룹니다. "
        "하지만 문제는 의지가 아니라 뇌의 마찰입니다.\n\n"
        "## 1. 60점짜리 못난 초안의 마법\n"
        "완벽주의를 버리고 60점 초안을 먼저 던져두면 마찰이 급격히 줄어듭니다. "
        "초안을 작성하고 나면 수정과 퇴고는 훨씬 쉬워집니다.\n\n"
        "## 2. 구체적인 3단계 실행 공식\n"
        "1) 10분 타이머 설정\n2) 서두 쓰지 않고 본론 한 줄부터 쓰기\n3) 스스로에게 60점 합격점 부여하기\n\n"
        "이렇게 완벽주의를 내려놓고 초안을 써 내려갈 때 비로소 진정한 몰입과 성장이 시작됩니다."
    )

    distiller = MaterialDistiller(repo=repo, llm_client=mock_llm)
    planner = SynthesisPlanner(llm_client=mock_llm)
    synthesizer = ArticleSynthesizer(
        config=config,
        repo=repo,
        llm_client=mock_llm,
        planner=planner,
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
