"""Style Learning and Persona Profile API router."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.auth import verify_auth
from src.api.schemas.style import (
    StyleLearnRequest,
    StyleLearnResponse,
    StyleProfileResponse,
    StyleUpdateRequest,
)
from src.config import load_config
from src.extraction.llm_client import LLMClient
from src.models import UserStyleProfile
from src.storage.repository import StorageRepository
from src.synthesis.style_learner import StyleLearner

router = APIRouter(prefix="/style", tags=["Style Learning"], dependencies=[Depends(verify_auth)])


@router.get("", response_model=StyleProfileResponse)
async def get_style_profile():
    """Retrieve the currently active UserStyleProfile."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
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
async def update_style_profile(req: StyleUpdateRequest):
    """Directly update style profile JSON."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
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
async def run_style_learning(req: StyleLearnRequest):
    """Analyze finalized user revisions to iteratively update persona style profile."""
    config = load_config()
    repo = StorageRepository(db_path=config.paths.db_path, processed_dir=config.paths.processed_dir)
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
            window_size=req.window_size,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Style learning execution failed: {e}",
        )

    if not profile:
        return StyleLearnResponse(
            success=False,
            learned_creations_count=0,
            updated_profile={},
            message=f"스타일 학습에 필요한 퇴고 완료 글(최소 {min_count}편)이 충분하지 않습니다. 퇴고 후 '저장'된 글이 있는지 확인해주세요.",
        )

    return StyleLearnResponse(
        success=True,
        learned_creations_count=profile.based_on_creation_count,
        updated_profile=profile.model_dump(),
        message=f"성공적으로 {profile.based_on_creation_count}편의 글로부터 글쓴이의 고유 스타일을 학습하여 반영했습니다.",
    )
