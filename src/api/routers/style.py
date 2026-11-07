"""Style Learning and Persona Profile API router."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.auth import verify_auth
from src.api.dependencies import ConfigDep, RepoDep
from src.api.schemas.style import (
    StyleLearnRequest,
    StyleLearnResponse,
    StyleProfileResponse,
    StyleUpdateRequest,
)
from src.extraction.llm_client import LLMClient
from src.models import UserStyleProfile
from src.synthesis.style_learner import StyleLearner

router = APIRouter(prefix="/style", tags=["Style Learning"], dependencies=[Depends(verify_auth)])


@router.get("", response_model=StyleProfileResponse)
async def get_style_profile(repo: RepoDep, config: ConfigDep):
    """Retrieve the currently active UserStyleProfile."""
    learner = StyleLearner(config=config, repo=repo)
    profile = learner.get_active_profile()

    if not profile:
        # Default baseline persona
        return StyleProfileResponse(
            persona_name="Chief Business Essayist",
            tone_and_manner=[
                "실무자의 언어로 말하는 냉철하지만 다정한 멘토 톤",
                "공허한 수사학 배제, 1인칭 현장 경험과 구체적 수치 제시",
                "모호한 아이디어를 실행 가능한 3단계 프레임워크로 재정의",
            ],
            sentence_style={
                "average_sentence_length": 45,
                "preferred_ending": "하십시오/합니다 (정중한 경어체와 단호한 평서체 혼용)",
                "paragraph_structure": "도입 훅 -> 반전/재정의 -> 실전 공식 -> 체크리스트",
            },
            vocabulary_profile={
                "core_keywords": ["본질", "프레임워크", "오버엔지니어링", "비즈니스 임팩트", "실행"],
            },
            storytelling_structures=[
                "실패/혼란의 현장 에피소드로 시작",
                "통념에 반대되는 새로운 관점(Reframing) 제시",
                "바로 실무에 적용 가능한 단계별 가이드라인",
            ],
            banned_patterns=[
                "~에 대해 알아보겠습니다와 같은 기계적인 블로그 도입부",
                "뜬구름 잡는 추상적 격언 나열",
            ],
            raw_profile={},
        )

    return StyleProfileResponse(
        persona_name=profile.persona_name,
        tone_and_manner=profile.tone_and_manner,
        sentence_style=profile.sentence_style,
        vocabulary_profile=profile.vocabulary_profile,
        storytelling_structures=profile.storytelling_structures,
        banned_patterns=profile.banned_patterns,
        raw_profile=profile.model_dump(),
    )


@router.put("", response_model=StyleProfileResponse)
async def update_style_profile(req: StyleUpdateRequest, repo: RepoDep, config: ConfigDep):
    """Directly update style profile JSON."""
    learner = StyleLearner(config=config, repo=repo)

    try:
        profile = UserStyleProfile.model_validate(req.profile_data)
        learner.profile_path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid style profile format: {e}",
        )

    return StyleProfileResponse(
        persona_name=profile.persona_name,
        tone_and_manner=profile.tone_and_manner,
        sentence_style=profile.sentence_style,
        vocabulary_profile=profile.vocabulary_profile,
        storytelling_structures=profile.storytelling_structures,
        banned_patterns=profile.banned_patterns,
        raw_profile=profile.model_dump(),
    )


@router.post("/learn", response_model=StyleLearnResponse)
async def run_style_learning(req: StyleLearnRequest, repo: RepoDep, config: ConfigDep):
    """Analyze finalized user revisions to iteratively update persona style profile."""
    llm = LLMClient()
    if not llm.api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API Key (GEMINI_API_KEY) is required to run style learning.",
        )

    learner = StyleLearner(config=config, repo=repo, llm_client=llm)
    min_count = req.min_finalized_count
    force_learning = req.force or (min_count <= 1)

    try:
        profile = await learner.learn_style(
            min_count=min_count,
            force=force_learning,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Style learning failed: {e}")

    return StyleLearnResponse(
        status="SUCCESS",
        learned_profile=StyleProfileResponse(
            persona_name=profile.persona_name,
            tone_and_manner=profile.tone_and_manner,
            sentence_style=profile.sentence_style,
            vocabulary_profile=profile.vocabulary_profile,
            storytelling_structures=profile.storytelling_structures,
            banned_patterns=profile.banned_patterns,
            raw_profile=profile.model_dump(),
        ),
        finalized_creations_used=min_count,
        message="사용자 최종 교정본 분석을 바탕으로 퍼소나 스타일 프로필을 성공적으로 학습/갱신했습니다.",
    )
