"""Automated unit tests for SynthesisPlanner domain logic."""

from unittest.mock import MagicMock
import pytest
from src.extraction.llm_client import LLMClient
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    SeedRoleAssignment,
    SynthesisBlueprint,
)
from src.synthesis.planner import SynthesisPlanner


@pytest.fixture
def sample_seeds():
    meta = ArticleMetadata(
        target_audience="주니어 기획자",
        core_problem="AI 코딩 도구의 오버엔지니어링",
        reframing_logic="도구가 아니라 목적 설정의 문제다",
        core_thesis="코딩은 AI가 하지만 목적은 기획자가 정한다",
        article_archetype=ArticleArchetype.STEP_BY_STEP_TUTORIAL,
        hook_strategy="비용 참사 통계",
        solution_framework=["목적 정의", "제약 설정", "검토"],
        notable_episodes=["300명 앱에 50만원 서버 청구"],
        reusable_asset_types=[],
        primary_category="기획",
        topic_tags=["AI", "기획", "비용"],
    )
    return [
        SeedRoleAssignment(
            seed_type="domain_case",
            doc_id="doc1",
            title="AI 기획 실무",
            reason="핵심 사례 제공",
            metadata=meta,
        )
    ]


def test_planner_sync_execution(sample_seeds):
    """Verify synchronous blueprint generation with mocked structured output."""
    mock_llm = MagicMock(spec=LLMClient)
    expected_blueprint = SynthesisBlueprint(
        proposed_title="AI 시대, 기획자의 진짜 역할",
        target_reader_definition="실무 기획자",
        synthesized_reframing="목적과 제약 설정이 AI 코딩의 성패를 가른다",
        role_assignments=["doc1에서 오버엔지니어링 비용 사례 차용"],
        section_outline=[
            "1. AI 만능주의의 함정: 300명 회원수첩 일화",
            "2. 도구가 아닌 목적의 부재: 진짜 문제 정의",
            "3. 기획자가 설정해야 할 3대 제약선",
        ],
    )
    mock_llm.extract_structured_sync.return_value = expected_blueprint

    planner = SynthesisPlanner(llm_client=mock_llm)
    res = planner.plan_blueprint_sync(
        topic="AI 기획자의 본질",
        direction="오버엔지니어링 통제",
        seeds=sample_seeds,
        archetype=ArticleArchetype.STEP_BY_STEP_TUTORIAL,
    )

    assert res.proposed_title == "AI 시대, 기획자의 진짜 역할"
    assert res.working_title == "AI 시대, 기획자의 진짜 역할"
    assert res.core_thesis == "목적과 제약 설정이 AI 코딩의 성패를 가른다"
    assert len(res.section_outline) == 3
    mock_llm.extract_structured_sync.assert_called_once()


def test_planner_archetype_fallback(sample_seeds):
    """Verify planner handles None archetype gracefully."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.extract_structured_sync.return_value = SynthesisBlueprint(
        proposed_title="테스트 제목",
        target_reader_definition="일반 독자",
        synthesized_reframing="테제",
        role_assignments=["요소1"],
        section_outline=["1. 서론"],
    )

    planner = SynthesisPlanner(llm_client=mock_llm)
    res = planner.plan_blueprint_sync(
        topic="테스트 주제",
        direction="",
        seeds=sample_seeds,
        archetype=None,
    )
    assert res.working_title == "테스트 제목"
    mock_llm.extract_structured_sync.assert_called_once()
