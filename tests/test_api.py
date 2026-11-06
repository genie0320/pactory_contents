"""Integration tests for Pactory Studio FastAPI REST API."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from src.api.auth import get_configured_password
from src.api.main import app

client = TestClient(app)
AUTH_PWD = get_configured_password()
AUTH_HEADERS = {"x-studio-password": AUTH_PWD} if AUTH_PWD else {}


def test_health_check():
    """Verify healthcheck endpoint returns 200 OK without auth."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"


def test_auth_rejection_and_login():
    """Verify auth rejection when password is required, and successful login."""
    status_resp = client.get("/api/auth/status")
    assert status_resp.status_code == 200
    auth_required = status_resp.json()["auth_required"]

    if auth_required:
        # Request without header should be rejected
        unauth_resp = client.get("/api/inbox/stats")
        assert unauth_resp.status_code == 401

        # Request with wrong password
        wrong_resp = client.get("/api/inbox/stats", headers={"x-studio-password": "wrong"})
        assert wrong_resp.status_code == 401

        # Login with correct password
        login_resp = client.post("/api/auth/login", json={"password": AUTH_PWD})
        assert login_resp.status_code == 200
        assert login_resp.json()["authenticated"] is True


def test_inbox_endpoints():
    """Verify inbox scan, stats, and articles endpoints."""
    # Stats
    stats_resp = client.get("/api/inbox/stats", headers=AUTH_HEADERS)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_articles" in stats
    assert "indexed_articles" in stats

    # Scan
    scan_resp = client.get("/api/inbox/scan", headers=AUTH_HEADERS)
    assert scan_resp.status_code == 200
    scan = scan_resp.json()
    assert "total_files" in scan
    assert "files" in scan

    # Articles
    articles_resp = client.get("/api/inbox/articles?limit=5", headers=AUTH_HEADERS)
    assert articles_resp.status_code == 200
    articles = articles_resp.json()
    assert "total" in articles
    assert "items" in articles


def test_seed_search_endpoint():
    """Verify draft seed candidate search."""
    resp = client.post(
        "/api/draft/seeds",
        json={"topic": "비즈니스 기획", "direction": "실무 실행력 강화", "limit": 5},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["topic"] == "비즈니스 기획"
    assert "candidates" in data


def test_creations_crud_lifecycle():
    """Verify full CRUD lifecycle for draft creations."""
    # 1. Create
    create_payload = {
        "topic": "API 테스트 주제",
        "direction": "테스트 방향성",
        "target_archetype": "PRACTICAL_GUIDE",
        "seed_doc_ids": [],
        "ai_draft_text": "# API 테스트 초안\n\n내용입니다.",
        "status": "DRAFT",
    }
    create_resp = client.post("/api/creations", json=create_payload, headers=AUTH_HEADERS)
    assert create_resp.status_code == 200
    created = create_resp.json()
    cid = created["creation_id"]
    assert cid.startswith("c_")
    assert created["topic"] == "API 테스트 주제"

    # 2. Get Detail
    get_resp = client.get(f"/api/creations/{cid}", headers=AUTH_HEADERS)
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["creation_id"] == cid
    assert detail["ai_draft_text"] == "# API 테스트 초안\n\n내용입니다."

    # 3. Update
    update_payload = {
        "user_final_text": "# API 테스트 개정본\n\n사용자가 수정한 최종본입니다.",
        "custom_notes": "테스트 메모",
        "status": "FINALIZED",
    }
    put_resp = client.put(f"/api/creations/{cid}", json=update_payload, headers=AUTH_HEADERS)
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["status"] == "FINALIZED"
    assert updated["user_final_text"] == update_payload["user_final_text"]

    # 4. List
    list_resp = client.get("/api/creations?limit=10", headers=AUTH_HEADERS)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(item["creation_id"] == cid for item in items)

    # 5. Delete
    del_resp = client.delete(f"/api/creations/{cid}", headers=AUTH_HEADERS)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Confirm deletion
    get_after = client.get(f"/api/creations/{cid}", headers=AUTH_HEADERS)
    assert get_after.status_code == 404


def test_style_endpoints():
    """Verify style profile retrieval."""
    resp = client.get("/api/style", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "persona_name" in data
    assert "tone_and_manner" in data


@patch("src.synthesis.proofreader.ArticleProofreader.review")
def test_proofread_endpoint_mocked(mock_review):
    """Verify proofreading endpoint with mocked LLM review."""
    mock_review.return_value = {
        "platform": "brunch",
        "mode": "report",
        "critique_report": "### 테스트 진단 리포트\n\n매우 훌륭한 구조입니다.",
        "rewritten_text": None,
        "hooking_score": 9,
        "balance_score": 9,
        "platform_score": 9,
        "suggested_title": "테스트 제목",
    }

    resp = client.post(
        "/api/proofread",
        json={
            "content": "# 테스트 글\n본문입니다.",
            "platform": "brunch",
            "mode": "report",
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["platform"] == "brunch"
    assert "테스트 진단 리포트" in data["critique_report"]
    assert data["hooking_score"] == 9


def test_observability_endpoint():
    """Verify observability stats endpoint returns aggregated metric keys."""
    resp = client.get("/api/observability/stats", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_calls" in data
    assert "total_tokens" in data
    assert "avg_latency_ms" in data
    assert "total_cost_usd" in data

