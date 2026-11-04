"""Pydantic v2 data models and schemas for the Seed Synthesis Engine."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ArticleArchetype(str, Enum):
    TRIAL_AND_ERROR_RETRO = "trial_and_error_retro"       # 1인칭 시행착오 및 프로젝트 회고형
    STEP_BY_STEP_TUTORIAL = "step_by_step_tutorial"       # 실전 구축 및 단계별 튜토리얼형
    FRAMEWORK_CHECKLIST = "framework_checklist"           # 실무 프로세스 및 체크리스트 제안형
    CASE_STUDY_WORKSHOP = "case_study_workshop"           # 다중 사례 분석 및 실습 워크숍형
    BRAND_INTERVIEW_QA = "brand_interview_qa"             # 브랜드/창업가 스토리 강연 및 Q&A형
    TEMPLATE_CURATION = "template_curation"               # 로드맵 기반 템플릿/도구 모음집형


class ReusableAssetType(str, Enum):
    PROMPT_TEMPLATE = "prompt_template"                   # 복붙 가능한 AI 프롬프트/지시문
    CHECKLIST_TABLE = "checklist_table"                   # 점검표 및 자가진단 리스트
    BEFORE_AFTER_COMPARISON = "before_after_comparison"   # 수정 전/후 비교 사례
    QUANTITATIVE_METRICS = "quantitative_metrics"         # 실제 매출, 전환율, 소요 시간 등 정량 수치
    FAILURE_EPISODE = "failure_episode"                   # 구체적 실패/반려/시행착오 에피소드
    STEP_DIAGRAM = "step_diagram"                         # 프로세스 도식 및 퍼널 설계도


class VisualAssetItem(BaseModel):
    asset_id: str = Field(..., description="이미지 파일 식별자 (예: img_p04_01)")
    page_no: int = Field(..., description="원본 PDF 페이지 번호")
    file_path: str = Field(..., description="processed/assets/ 내 상대 경로")
    caption: str = Field(default="", description="이미지 하단 또는 주변에서 추출된 캡션 텍스트")
    width: int = Field(..., description="이미지 가로 폭 (px)")
    height: int = Field(..., description="이미지 세로 높이 (px)")


class VisualAssetManifest(BaseModel):
    doc_id: str
    assets: List[VisualAssetItem] = Field(default_factory=list)


class ArticleMetadata(BaseModel):
    # 1. 타깃 및 문제의식 (Target & Problem)
    target_audience: str = Field(
        ..., description="이 글이 가장 유효하게 작용하는 구체적 타깃 독자 페르소나 및 처한 상황 (1~2문장)"
    )
    core_problem: str = Field(
        ..., description="독자가 겪고 있는 표면적 막막함 또는 글이 해결하려는 핵심 질문 (1~2문장)"
    )

    # 2. 관점 전환 및 핵심 테제 (Perspective & Reframing Seed)
    reframing_logic: str = Field(
        ..., description="통념을 뒤집는 관점의 전환 공식 ('문제가 A인 줄 알았는데 실제로는 B였다' 형태, 1~2문장)"
    )
    core_thesis: str = Field(
        ..., description="글 전체를 관통하는 단 하나의 핵심 결론 문장"
    )

    # 3. 서사 구조 및 해결 프레임워크 (Structure & Framework Seed)
    article_archetype: ArticleArchetype = Field(
        ..., description="글의 전체 전개 방식 및 장르 유형"
    )
    hook_strategy: str = Field(
        ..., description="도입부에서 독자의 시선을 끄는 방식 (예: 수치 공개, 실패담 고백, 자가진단 체크리스트 등)"
    )
    solution_framework: List[str] = Field(
        ..., min_length=2, max_length=6,
        description="글이 제시하는 단계별 실행 방법론 또는 핵심 프레임워크 (3~5개 항목 리스트)"
    )

    # 4. 재사용 재료 및 분류 태그 (Material & Taxonomy Seed)
    notable_episodes: List[str] = Field(
        ..., min_length=1, max_length=4,
        description="새 글에 인용하기 좋은 구체적 사례, 시행착오 에피소드, 정량적 실험 결과 요약 (1~3개)"
    )
    reusable_asset_types: List[ReusableAssetType] = Field(
        default_factory=list,
        description="본문 내 포함된 실무 도구/근거 블록 유형 리스트"
    )
    primary_category: str = Field(
        ..., description="대분류 도메인 (예: 업무스킬, 서비스기획/AI, 마케팅/브랜딩, 커리어/이직, 부업/수익화, 자기관리)"
    )
    topic_tags: List[str] = Field(
        ..., min_length=3, max_length=7,
        description="글의 핵심 소재 및 키워드 태그 (3~7개)"
    )


class ArticleStatus(str, Enum):
    INGESTED = "INGESTED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class ArticleRecord(BaseModel):
    doc_id: str
    title: str
    author: str = ""
    published_date: str = ""
    source_format: str  # 'pdf', 'md', 'txt'
    original_path: str
    processed_text_path: str
    assets_dir_path: str = ""
    content_hash: str
    char_count: int
    image_count: int = 0
    status: ArticleStatus = ArticleStatus.INGESTED
    error_msg: str = ""
    ingested_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None


class SynthesisBlueprint(BaseModel):
    """초안 작성 전 선별된 Seed들을 어떻게 엮을지 정의하는 합성 설계도"""
    proposed_title: str = Field(..., description="새로 작성할 아티클의 가제")
    target_reader_definition: str = Field(..., description="새 글의 타깃 독자 및 핵심 페인포인트")
    synthesized_reframing: str = Field(..., description="Seed들의 관점을 결합하여 도출한 새 글만의 핵심 관점 전환 명제")
    role_assignments: List[str] = Field(..., description="각 Seed 문서(doc_id)에서 차용할 구체적 요소 (문제제기/프레임워크/사례 등) 명시")
    section_outline: List[str] = Field(..., description="새 글의 섹션별 소제목 및 핵심 내용 구성안 (4~6개 섹션)")
    visual_asset_recommendations: List[str] = Field(
        default_factory=list,
        description="선별된 Seed의 이미지(asset_id) 중 어느 섹션에 어떤 형태로 재구성/삽입하면 좋을지 제안",
    )


class DistilledMaterialSheet(BaseModel):
    """[v2.0] 초안이 Seed의 문장과 포맷을 모방하지 않도록 원문에서 알맹이만 발췌한 건조한 개조식 재료 시트"""
    doc_id: str
    assigned_role: str = Field(..., description="이 Seed가 새 글에서 맡은 역할 (소재/사례 vs 관점/논리 vs 실무도구)")
    core_mechanism_bullets: List[str] = Field(
        ..., description="원문의 문체를 완전히 제거하고 인과관계와 작동 원리만 건조한 명사형/개조식으로 요약한 리스트"
    )
    extracted_facts_and_numbers: List[str] = Field(
        ..., description="인용 가능한 정량 수치, 소요 기간, 전후 변화 데이터, 실험 조건"
    )
    case_causal_chains: List[str] = Field(
        ..., description="[상황 -> 문제 발생 -> 개입/해결책 -> 결과] 구조로만 축약한 에피소드 뼈대 (원문 어투 배제)"
    )
    raw_templates_or_criteria: List[str] = Field(
        default_factory=list, description="체크리스트 판단 기준, 프롬프트 핵심 조건 등 새 글의 도메인에 맞게 치환할 원재료"
    )


class UserStyleProfile(BaseModel):
    """[v2.0] 사용자가 직접 수정해 저장한 '나의 결과물' 5편 이상의 Diff에서 추출한 나만의 스타일 규칙"""
    profile_version: int = Field(default=1)
    based_on_creation_count: int = Field(..., description="분석에 사용된 내 결과물 개수 (최소 5개 권장)")
    preferred_tone_and_endings: List[str] = Field(..., description="선호하는 종결어미, 문장 길이, 호흡 규칙")
    structural_preferences: List[str] = Field(..., description="도입부 시작 방식, 소제목 네이밍 패턴, 단락 구성 특징")
    forbidden_patterns: List[str] = Field(..., description="사용자가 수정 과정에서 반복적으로 삭제·기피한 AI/Seed 특유 표현이나 포맷")
    signature_formatting_rules: List[str] = Field(..., description="사용자가 즐겨 쓰는 강조 방식, 리스트/표 배치 규칙")


class SeedRoleAssignment(BaseModel):
    seed_type: str  # "domain_case" | "perspective_framework" | "structure_asset"
    doc_id: str
    title: str
    reason: str
    metadata: ArticleMetadata
