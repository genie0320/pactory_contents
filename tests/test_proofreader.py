import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
import pytest
from src.exceptions import LLMServiceError
from src.extraction.llm_client import LLMClient
from src.synthesis.proofreader import ArticleProofreader

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mock_proofreader_payload.json"
with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
    FIXTURES = json.load(f)

SAMPLE_TEXT = """# 실전 비즈니스 기획의 본질

아이디어만으로는 시장에서 승부할 수 없습니다.
복잡한 생각을 덜어내고 단 하나의 날카로운 칼날처럼 다듬는 3단계 공식이 필요합니다.

1단계: 본질의 언어화
2단계: 모호함을 걷어내는 극단적 구체화
3단계: 피드백의 칼날 위에서 깎아내기
"""


def test_split_frontmatter():
    text_with_fm = """---
title: 테스트 제목
topic: AI 기획
---
# 본문 시작
본문 내용입니다.
"""
    fm, body = ArticleProofreader.split_frontmatter(text_with_fm)
    assert "title: 테스트 제목" in fm
    assert fm.startswith("---") and fm.endswith("---")
    assert body.startswith("# 본문 시작")
    assert "---" not in body

    # Plain text without frontmatter
    text_plain = "# 제목\n내용"
    fm2, body2 = ArticleProofreader.split_frontmatter(text_plain)
    assert fm2 == ""
    assert body2 == "# 제목\n내용"


def test_proofreader_raises_when_no_api_key():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.api_key = ""
    proofreader = ArticleProofreader(llm_client=mock_llm)

    with pytest.raises(LLMServiceError) as exc_info:
        proofreader.review_sync(content=SAMPLE_TEXT, mode="report")
    assert "API key is required" in str(exc_info.value)


def test_proofreader_report_mode_with_mock():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.api_key = "fake-key"
    mock_llm.generate_text_sync.return_value = FIXTURES["sample_critique_report"]

    proofreader = ArticleProofreader(llm_client=mock_llm)
    res = proofreader.review_sync(
        content=SAMPLE_TEXT,
        platform="brunch",
        mode="report",
    )

    assert res["platform"] == "brunch"
    assert res["mode"] == "report"
    assert "에디토리얼 진단 리포트" in res["critique_report"]
    assert res["rewritten_text"] is None
    assert res["suggested_title"] == "실전 비즈니스 기획의 본질"
    mock_llm.generate_text_sync.assert_called_once()


def test_proofreader_rewrite_mode_with_mock():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.api_key = "fake-key"
    mock_llm.generate_text_sync.return_value = FIXTURES["sample_rewrite_brunch"]

    proofreader = ArticleProofreader(llm_client=mock_llm)
    res = proofreader.review_sync(
        content=SAMPLE_TEXT,
        platform="brunch",
        mode="rewrite",
    )

    assert res["platform"] == "brunch"
    assert res["mode"] == "rewrite"
    assert res["rewritten_text"] == FIXTURES["sample_rewrite_brunch"]
    assert res["suggested_title"] == "테스트 브런치 개정본"
    mock_llm.generate_text_sync.assert_called_once()


def test_proofreader_async_review():
    import asyncio
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.api_key = "fake-key"
    mock_llm.generate_text = AsyncMock(return_value=FIXTURES["sample_rewrite_threads"])

    proofreader = ArticleProofreader(llm_client=mock_llm)
    res = asyncio.run(proofreader.review(
        content=SAMPLE_TEXT,
        platform="threads",
        mode="rewrite",
    ))

    assert res["platform"] == "threads"
    assert res["mode"] == "rewrite"
    assert res["rewritten_text"] == FIXTURES["sample_rewrite_threads"]
    assert res["suggested_title"] == "테스트 스레드 개정본"
    mock_llm.generate_text.assert_awaited_once()
