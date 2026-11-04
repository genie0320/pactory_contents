"""Tests for SeedRetriever: FTS5 BM25 search and role-based complementary ranking (Milestone 4)."""

from pathlib import Path
import pytest

from src.config import AppConfig, PathSettings
from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    ArticleRecord,
    ArticleStatus,
    ReusableAssetType,
)
from src.storage.db import init_db
from src.storage.repository import StorageRepository
from src.storage.retriever import SeedRetriever


@pytest.fixture
def populated_retriever(tmp_path: Path):
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

    # 1. Seed #1 Candidate: Domain & Case Rich (AI 자동화 실패와 성공 사례)
    meta1 = ArticleMetadata(
        target_audience="업무 자동화에 실패했던 주니어 기획자",
        core_problem="도구를 사내에 도입해도 팀원들이 쓰지 않고 방치됨",
        reframing_logic="도구의 문제가 아니라 심리적 마찰의 문제다",
        core_thesis="업무 자동화의 핵심은 기술이 아니라 팀원의 심리적 마찰 해소다",
        article_archetype=ArticleArchetype.TRIAL_AND_ERROR_RETRO,
        hook_strategy="유입 0건 통계 공개",
        solution_framework=["마찰 식별", "1초 버튼 배치", "즉시 피드백"],
        notable_episodes=[
            "도입 초기 1주간 활성 유저 0명에서 무료 진단 버튼 추가 후 팀 전체 100% 사용 전환",
            "슬랙 봇 커맨드 간소화로 하루 문의 처리량 400% 급증",
        ],
        reusable_asset_types=[ReusableAssetType.QUANTITATIVE_METRICS, ReusableAssetType.FAILURE_EPISODE],
        primary_category="서비스기획/AI",
        topic_tags=["AI자동화", "사내도입", "업무효율", "프롬프트", "운영관리"],
    )
    repo.save_processed_text("8194", "# AI 서비스 첫 판매기\n\n초기 유입 0건의 실패를 겪고...")
    art1 = ArticleRecord(
        doc_id="8194",
        title="비개발자 실무자의 사내 AI 자동화 도입기",
        source_format="md",
        original_path="archive/8194.md",
        processed_text_path="processed/texts/8194.md",
        content_hash="h1",
        char_count=2000,
    )
    repo.upsert_article(art1)
    repo.save_article_metadata("8194", meta1, title=art1.title)

    # 2. Seed #2 Candidate: Perspective & Framework Rich (마찰 제거 및 루틴 형성)
    meta2 = ArticleMetadata(
        target_audience="새로운 습관을 정착시키지 못하는 직장인",
        core_problem="의지와 결심만으로는 행동이 3일을 넘기지 못함",
        reframing_logic="의지가 아니라 마찰의 문제이므로 1초 컷 가짜 성취감을 설계하라",
        core_thesis="마찰을 극한으로 낮추면 의지 없이도 시스템이 작동한다",
        article_archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
        hook_strategy="작심삼일 통계 제시",
        solution_framework=[
            "1단계: 행동 직전 물리적 마찰 제거",
            "2단계: 최소 단위 1초 실행 장치 마련",
            "3단계: 가짜 성취감 기록 루프 형성",
        ],
        notable_episodes=["독서 루틴 실패담 극복 후 연 50권 완독"],
        reusable_asset_types=[ReusableAssetType.STEP_DIAGRAM],
        primary_category="자기관리",
        topic_tags=["마찰제거", "루틴설계", "습관형성", "생산성", "행동설계"],
    )
    repo.save_processed_text("8195", "# 습관 형성 치트키\n\n마찰을 제거하는 3단계 공식...")
    art2 = ArticleRecord(
        doc_id="8195",
        title="의지 없이 지속하는 마찰 최소화 루틴 설계법",
        source_format="md",
        original_path="archive/8195.md",
        processed_text_path="processed/texts/8195.md",
        content_hash="h2",
        char_count=2500,
    )
    repo.upsert_article(art2)
    repo.save_article_metadata("8195", meta2, title=art2.title)

    # 3. Seed #3 Candidate: Structure & Practical Assets (체크리스트, 역산 템플릿)
    meta3 = ArticleMetadata(
        target_audience="프로젝트 마감과 실행에 쫓기는 PM 및 마케터",
        core_problem="D-day 직전에 업무가 몰리고 누락이 발생함",
        reframing_logic="순방향 계획은 지연을 부르므로 D-90 역산 체크리스트로 통제해야 한다",
        core_thesis="역산 기획표가 프로젝트 성공의 90%를 결정한다",
        article_archetype=ArticleArchetype.STEP_BY_STEP_TUTORIAL,
        hook_strategy="론칭 당일 서버 폭파 사고 회고",
        solution_framework=["D-90 핵심 가설 정의", "D-30 프로토타입 점검", "D-7 배포 리허설"],
        notable_episodes=["D-90 역산 표 도입 후 런칭 지연 0건 달성"],
        reusable_asset_types=[ReusableAssetType.CHECKLIST_TABLE, ReusableAssetType.PROMPT_TEMPLATE],
        primary_category="업무스킬",
        topic_tags=["역산기획", "체크리스트", "프로젝트관리", "일정관리", "실무템플릿"],
    )
    repo.save_processed_text("8204", "# 연말 프로모션 D-90 역산 기획\n\n체크리스트 표와 단계별 튜토리얼...")
    art3 = ArticleRecord(
        doc_id="8204",
        title="D-90 역산 기획 체크리스트 및 실전 가이드",
        source_format="md",
        original_path="archive/8204.md",
        processed_text_path="processed/texts/8204.md",
        content_hash="h3",
        char_count=2200,
    )
    repo.upsert_article(art3)
    repo.save_article_metadata("8204", meta3, title=art3.title)

    retriever = SeedRetriever(config=config, repo=repo)
    return retriever


def test_jaccard_and_keyword_extraction():
    tokens = SeedRetriever.extract_keywords("사이드 프로젝트를 지속하고 마찰을 줄이는 방법")
    assert "사이드" in tokens
    assert "프로젝트" in tokens
    assert "마찰" in tokens

    jaccard = SeedRetriever.jaccard_similarity(["AI", "자동화", "도입"], ["마찰", "루틴", "습관"])
    assert jaccard == 0.0

    jaccard_half = SeedRetriever.jaccard_similarity(["AI", "마찰"], ["AI", "루틴"])
    assert 0.3 < jaccard_half < 0.4


def test_complementary_seed_selection(populated_retriever):
    retriever = populated_retriever
    seeds = retriever.select_complementary_seeds(
        topic="비개발자 실무자의 사내 AI 자동화 도입기",
        direction="도구 자랑이 아니라 팀원들이 실제로 쓰게 만드는 운영과 마찰 제거",
        target_archetype=ArticleArchetype.TRIAL_AND_ERROR_RETRO,
        count=3,
    )

    assert len(seeds) == 3

    # Check Seed #1 role: domain_case
    assert seeds[0].seed_type == "domain_case"
    assert seeds[0].doc_id == "8194"

    # Check Seed #2 role: perspective_framework (should pick complementary perspective 8195)
    assert seeds[1].seed_type == "perspective_framework"
    assert seeds[1].doc_id == "8195"

    # Check Seed #3 role: structure_asset (should pick checklist / tutorial 8204)
    assert seeds[2].seed_type == "structure_asset"
    assert seeds[2].doc_id == "8204"
