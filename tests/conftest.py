"""Global pytest fixtures and mock LLM clients for offline deterministic testing."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.extraction.llm_client import LLMClient
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    DistilledMaterialSheet,
    ReusableAssetType,
    SynthesisBlueprint,
    UserStyleProfile,
)


@pytest.fixture
def sample_article_metadata() -> ArticleMetadata:
    return ArticleMetadata(
        primary_category="서비스기획/AI",
        article_archetype=ArticleArchetype.STEP_BY_STEP_TUTORIAL,
        target_audience="실무 기획자 및 주니어 PM",
        core_problem="AI 자동화 도입 시 구체적인 프로세스 및 시행착오 부재",
        reframing_logic="기술 스택보다 업무 흐름의 마찰 지점을 식별하는 것이 우선",
        core_thesis="업무 자동화의 핵심은 10초 착수 규칙과 비동기 문서화에 있다",
        hook_strategy="실제 업무 비효율 에피소드 제시",
        solution_framework=["1단계: 마찰점 식별", "2단계: 최소 파이프라인 구성", "3단계: 피드백 반영"],
        notable_episodes=["회의 시간 70% 단축 사례", "반복 수작업 3시간 단축"],
        reusable_asset_types=[ReusableAssetType.QUANTITATIVE_METRICS, ReusableAssetType.STEP_DIAGRAM],
        topic_tags=["AI", "자동화", "업무효율", "기획"],
    )


@pytest.fixture
def sample_blueprint() -> SynthesisBlueprint:
    return SynthesisBlueprint(
        proposed_title="실전 AI 자동화 파이프라인 구축 가이드",
        target_reader_definition="AI를 업무에 실질적으로 적용하려는 1~3년차 기획자",
        synthesized_reframing="도구 선택이 아니라 마찰 지점의 단순화가 성공을 결정한다",
        role_assignments=["도메인 사례 시드: 회의 단축", "프레임워크 시드: 3단계 공식"],
        section_outline=[
            "1. 왜 우리의 AI 도입은 번번이 흐지부지되는가",
            "2. 마찰 0의 파이프라인 구축 3단계 프레임워크",
            "3. 바로 적용 가능한 체크리스트와 핵심 지표",
        ],
    )


@pytest.fixture
def sample_style_profile() -> UserStyleProfile:
    return UserStyleProfile(
        profile_version=1,
        based_on_creation_count=5,
        preferred_tone_and_endings=["~다 위주의 간결한 단문", "군더더기 없는 종결"],
        structural_preferences=["도입부에서 문제 상황 극단적 대조", "단락별 핵심 문장 우선 배치"],
        forbidden_patterns=["~라고 생각된다", "이모지 남발", "요약 박스 중복"],
        signature_formatting_rules=["핵심 수치는 굵게 강조", "3단계 번호 리스트 활용"],
    )


def _default_schema_instance(schema):
    if schema == ArticleMetadata:
        return ArticleMetadata(
            primary_category="서비스기획/AI",
            article_archetype=ArticleArchetype.STEP_BY_STEP_TUTORIAL,
            target_audience="실무 기획자",
            core_problem="업무 비효율",
            reframing_logic="마찰 최소화",
            core_thesis="비동기 자동화 도입",
            hook_strategy="실화 기반 에피소드",
            solution_framework=["1단계", "2단계"],
            notable_episodes=["성공 사례 1"],
            reusable_asset_types=[ReusableAssetType.QUANTITATIVE_METRICS],
            topic_tags=["AI", "자동화", "업무효율"],
        )
    elif schema == DistilledMaterialSheet:
        return DistilledMaterialSheet(
            doc_id="mock_doc",
            assigned_role="domain_case",
            core_mechanism_bullets=["과업 착수 시 마찰 최소화"],
            extracted_facts_and_numbers=["생산성 3배 향상"],
            case_causal_chains=["상황 -> 문제 -> 해결 -> 결과"],
            raw_templates_or_criteria=["핵심 판단 기준"],
        )
    elif schema == SynthesisBlueprint:
        return SynthesisBlueprint(
            proposed_title="모의 기획안 초안",
            target_reader_definition="실무 기획자",
            synthesized_reframing="새로운 관점 제시",
            role_assignments=["시드 1"],
            section_outline=["1. 서론", "2. 본론", "3. 결론"],
        )
    elif schema == UserStyleProfile:
        return UserStyleProfile(
            profile_version=1,
            based_on_creation_count=5,
            preferred_tone_and_endings=["~다"],
            structural_preferences=["문제-해결-실행"],
            forbidden_patterns=["~인 것 같다"],
            signature_formatting_rules=["번호 리스트 활용"],
        )
    try:
        return schema()
    except Exception:
        return MagicMock()


@pytest.fixture
def mock_llm_client(sample_article_metadata, sample_blueprint, sample_style_profile):
    """Provides a fully mocked LLMClient instance that never calls external networks."""
    client = MagicMock(spec=LLMClient)
    client.api_key = "mock-api-key"
    client.provider = "gemini"
    client.model = "gemini-3.5-flash-lite"

    # Async extract_structured
    async def _async_extract(system_prompt="", user_prompt="", schema=None, model=None):
        return _default_schema_instance(schema)

    # Sync extract_structured_sync
    def _sync_extract(system_prompt="", user_prompt="", schema=None, model=None):
        return _default_schema_instance(schema)

    client.extract_structured = AsyncMock(side_effect=_async_extract)
    client.extract_structured_sync = MagicMock(side_effect=_sync_extract)

    # Text generation
    mock_draft_text = (
        "# 실전 AI 자동화 파이프라인 구축 가이드\n\n"
        "AI를 도입할 때 가장 흔히 겪는 실패는 기술의 복잡도 때문이 아닙니다.\n\n"
        "## 1. 마찰점 식별과 단순화\n"
        "업무의 흐름을 쪼개고 병목을 수치화하는 것이 시작입니다.\n\n"
        "## 2. 결론 및 체크리스트\n"
        "모든 단계를 기록하고 공유하세요."
    )
    client.generate_text = AsyncMock(return_value=mock_draft_text)
    client.generate_text_sync = MagicMock(return_value=mock_draft_text)

    # Embedding
    pseudo_vec = [0.25] * 16
    client.get_embedding = AsyncMock(return_value=pseudo_vec)
    client.get_embedding_sync = MagicMock(return_value=pseudo_vec)

    return client
