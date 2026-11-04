"""Unit and integration tests for SQLite and FTS5 storage layer (Milestone 1)."""

import time
from pathlib import Path
import pytest

from src.models import (
    ArticleArchetype,
    ArticleMetadata,
    ArticleRecord,
    ArticleStatus,
    ReusableAssetType,
    VisualAssetItem,
)
from src.storage.db import get_connection, init_db
from src.storage.repository import StorageRepository


@pytest.fixture
def temp_storage(tmp_path: Path):
    db_path = tmp_path / "index" / "catalog.db"
    processed_dir = tmp_path / "processed"
    init_db(db_path)
    repo = StorageRepository(db_path=db_path, processed_dir=processed_dir)
    return repo, db_path


def test_init_db_creates_tables(temp_storage):
    repo, db_path = temp_storage
    assert db_path.exists()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    tables = {
        row[0]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' OR type='shadow'"
        ).fetchall()
    }
    conn.close()

    assert "articles" in tables
    assert "article_metadata" in tables
    assert "article_assets" in tables
    assert "metadata_fts" in tables


def test_article_crud(temp_storage):
    repo, _ = temp_storage
    article = ArticleRecord(
        doc_id="8194",
        title="AI 서비스 첫 판매기",
        author="하루",
        published_date="2025-01-15",
        source_format="pdf",
        original_path="data/archive/8194_test.pdf",
        processed_text_path="data/processed/texts/8194.md",
        content_hash="hash8194abcdef",
        char_count=3500,
        image_count=2,
        status=ArticleStatus.INGESTED,
    )
    repo.upsert_article(article)

    retrieved = repo.get_article("8194")
    assert retrieved is not None
    assert retrieved.title == "AI 서비스 첫 판매기"
    assert retrieved.status == ArticleStatus.INGESTED

    by_hash = repo.get_article_by_hash("hash8194abcdef")
    assert by_hash is not None
    assert by_hash.doc_id == "8194"


def test_visual_assets_and_manifest(temp_storage):
    repo, _ = temp_storage
    # Seed an article first
    article = ArticleRecord(
        doc_id="8194",
        title="AI 서비스 첫 판매기",
        source_format="pdf",
        original_path="path",
        processed_text_path="path",
        content_hash="hash1",
        char_count=1000,
    )
    repo.upsert_article(article)

    assets = [
        VisualAssetItem(
            asset_id="img_p01_01",
            page_no=1,
            file_path="8194/img_p01_01.png",
            caption="║ 결과와 출처를 붙여 답해요. ©하루",
            width=600,
            height=400,
        ),
        VisualAssetItem(
            asset_id="img_p02_01",
            page_no=2,
            file_path="8194/img_p02_01.png",
            caption="║ 전환율 분석 퍼널",
            width=800,
            height=450,
        ),
    ]
    manifest_path = repo.save_visual_assets("8194", assets)
    assert manifest_path.exists()

    loaded_assets = repo.get_visual_assets("8194")
    assert len(loaded_assets) == 2
    assert loaded_assets[0].asset_id == "img_p01_01"

    updated_article = repo.get_article("8194")
    assert updated_article.image_count == 2


def test_fts5_indexing_and_speed_criteria(temp_storage):
    """
    Verification Criteria:
    catalog.db 생성 및 FTS5 한글/영문 키워드 MATCH 쿼리가 50ms 이내 정상 동작함
    """
    repo, db_path = temp_storage

    # Insert 10 diverse articles
    articles_data = [
        (
            "8194",
            "비개발자 실무자의 사내 AI 자동화 도입기",
            "자동화 업무스킬 AI도구",
            ArticleMetadata(
                target_audience="반복 업무에 지친 비개발자 기획자 및 실무진",
                core_problem="사내에 AI 도구를 도입해도 팀원들이 쓰지 않고 방치됨",
                reframing_logic="도구 자랑이 아니라 팀원들이 실제로 쓰게 만드는 운영과 신뢰 장치에 집중해야 한다",
                core_thesis="업무 자동화의 핵심은 기술이 아니라 팀원의 심리적 마찰 해소다",
                article_archetype=ArticleArchetype.TRIAL_AND_ERROR_RETRO,
                hook_strategy="실패담 고백 및 유입 0건 통계 공개",
                solution_framework=["1단계: 작은 마찰 식별", "2단계: 1초 컷 진입장벽 제거", "3단계: 신뢰 피드백 루프"],
                notable_episodes=["초기 유입 0건 실패담과 무료 가치 우선 제공 퍼널 구축"],
                reusable_asset_types=[ReusableAssetType.PROMPT_TEMPLATE, ReusableAssetType.FAILURE_EPISODE],
                primary_category="서비스기획/AI",
                topic_tags=["AI자동화", "사내도입", "업무효율", "프롬프트", "조직문화"],
            ),
        ),
        (
            "8195",
            "독서 기록 습관 치트키",
            "자기관리 습관 루틴",
            ArticleMetadata(
                target_audience="책을 사놓고 끝까지 읽지 못하는 직장인",
                core_problem="의지박약으로 인해 독서 루틴이 매번 작심삼일로 끝남",
                reframing_logic="의지의 문제가 아니라 마찰의 문제이므로 1초 컷 가짜 성취감을 설계해야 한다",
                core_thesis="환경을 통제하면 의지 없이도 행동이 유지된다",
                article_archetype=ArticleArchetype.FRAMEWORK_CHECKLIST,
                hook_strategy="독서 실패 통계 제시",
                solution_framework=["책장 위치 재설계", "한 페이지 읽기 규칙", "노션 템플릿 기록"],
                notable_episodes=["노션 템플릿 도입 후 월 4권 완독 달성"],
                reusable_asset_types=[ReusableAssetType.CHECKLIST_TABLE],
                primary_category="자기관리",
                topic_tags=["독서습관", "루틴설계", "마찰제거", "노션", "생산성"],
            ),
        ),
    ]

    for doc_id, title, tags, meta in articles_data:
        article = ArticleRecord(
            doc_id=doc_id,
            title=title,
            source_format="pdf",
            original_path=f"data/archive/{doc_id}.pdf",
            processed_text_path=f"data/processed/texts/{doc_id}.md",
            content_hash=f"hash_{doc_id}",
            char_count=2000,
        )
        repo.upsert_article(article)
        repo.save_article_metadata(doc_id=doc_id, metadata=meta, title=title)

        # Check status transition to INDEXED
        saved_article = repo.get_article(doc_id)
        assert saved_article.status == ArticleStatus.INDEXED

    # Test FTS5 Korean Search Query and Performance (< 50ms)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    queries = [
        "자동화",
        "AI",
        "루틴설계",
        "마찰",
        "Prompt",
        "체크리스트",
    ]

    for q in queries:
        start_time = time.perf_counter()
        # unicode61 match query
        cursor.execute(
            """
            SELECT doc_id, bm25(metadata_fts) as rank
            FROM metadata_fts
            WHERE metadata_fts MATCH ?
            ORDER BY rank
            """,
            (q,),
        )
        results = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Assert performance criterion: < 50ms
        assert elapsed_ms < 50.0, f"Query '{q}' took {elapsed_ms:.2f}ms, exceeding 50ms limit!"

    # Verify Korean keyword match results
    cursor.execute("SELECT doc_id FROM metadata_fts WHERE metadata_fts MATCH '자동화'")
    hits = [r["doc_id"] for r in cursor.fetchall()]
    assert "8194" in hits

    cursor.execute("SELECT doc_id FROM metadata_fts WHERE metadata_fts MATCH '루틴설계'")
    hits = [r["doc_id"] for r in cursor.fetchall()]
    assert "8195" in hits

    # Verify English keyword match results
    cursor.execute("SELECT doc_id FROM metadata_fts WHERE metadata_fts MATCH 'AI'")
    hits = [r["doc_id"] for r in cursor.fetchall()]
    assert "8194" in hits

    conn.close()
