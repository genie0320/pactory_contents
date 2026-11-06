import pytest
from src.extraction.llm_client import LLMClient
from src.synthesis.proofreader import ArticleProofreader

SAMPLE_TEXT = """# 기깔나는 '아이디어'만으로는 승부할 수 없다

올 초 하루 8시간 6개월동안의 부트캠프라는 어마어마한 대장정을 시작한 것은, 홀로 AI라는 급물살에 올라타기가 쉽지 않다는 것을 실감했기때문입니다.
비IT인들을 위한 IT번역도구를 꿈꿨던 저의 프로덕트는 부트캠프를 끝내고도 2개월이 지난 지금까지도 바이브코딩의 망망대해를 떠돌고 있는 참입니다.

동료들에게 물었을 때 돌아온 대답은 모호하다는 것이었습니다.

1단계: 본질의 언어화
2단계: 모호함을 걷어내는 극단적 구체화
3단계: 피드백의 칼날 위에서 깎아내기

- [ ] 내 비즈니스 컨셉을 15초 안에 설명할 수 있는가?
"""

def test_proofreader_report_mode():
    proofreader = ArticleProofreader(llm_client=LLMClient(api_key=""))
    res = proofreader.review_sync(
        content=SAMPLE_TEXT,
        platform="brunch",
        mode="report",
    )
    assert res["platform"] == "brunch"
    assert res["mode"] == "report"
    assert "에디토리얼 진단 리포트" in res["critique_report"]
    assert res["hooking_score"] >= 7
    assert res["balance_score"] >= 7
    assert res["rewritten_text"] is None

def test_proofreader_rewrite_mode_all_platforms():
    proofreader = ArticleProofreader(llm_client=LLMClient(api_key=""))
    for platform in ["threads", "linkedin", "brunch", "general"]:
        res = proofreader.review_sync(
            content=SAMPLE_TEXT,
            platform=platform,
            mode="rewrite",
        )
        assert res["platform"] == platform
        assert res["rewritten_text"] is not None
        assert len(res["rewritten_text"]) > 100
        assert "아이디어" in res["rewritten_text"]

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

def test_proofreader_episode2_ai_planning():
    proofreader = ArticleProofreader(llm_client=LLMClient(api_key=""))
    ep2_text = """# "기획은 AI가 잘해요" 정말 그럴까요?
300명이 이용하는 회원수첩앱에 한달 이용료가 50만원이나 나오는 클라우드 스펙 오버엔지니어링.
코딩은 AI가 너무 잘하지만 목적과 방향은 기획자가 설정해야 합니다.
"""
    res = proofreader.review_sync(
        content=ep2_text,
        platform="threads",
        mode="rewrite",
        critique_feedback="도입부 훅을 강화하고 댓글 유도 질문을 추가해줘",
    )
    assert res["rewritten_text"] is not None
    assert "회원수첩" in res["rewritten_text"] or "기획은 AI" in res["rewritten_text"]
    assert "300명" in res["rewritten_text"]
    assert "오버엔지니어링" in res["critique_report"]
