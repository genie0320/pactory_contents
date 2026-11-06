"""Database initialization and connection management for SQLite3 and FTS5."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

DDL_STATEMENTS = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. 문서 레지스트리 및 전처리 상태 관리 테이블
CREATE TABLE IF NOT EXISTS articles (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    published_date TEXT DEFAULT '',
    source_format TEXT NOT NULL,
    original_path TEXT NOT NULL,
    processed_text_path TEXT NOT NULL,
    assets_dir_path TEXT DEFAULT '',
    content_hash TEXT NOT NULL UNIQUE,
    char_count INTEGER NOT NULL,
    image_count INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'INGESTED',
    error_msg TEXT DEFAULT '',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP
);

-- 2. 구조화된 Seed 메타데이터 테이블
CREATE TABLE IF NOT EXISTS article_metadata (
    doc_id TEXT PRIMARY KEY,
    primary_category TEXT NOT NULL,
    article_archetype TEXT NOT NULL,
    target_audience TEXT NOT NULL,
    core_problem TEXT NOT NULL,
    reframing_logic TEXT NOT NULL,
    core_thesis TEXT NOT NULL,
    hook_strategy TEXT NOT NULL,
    solution_framework_json TEXT NOT NULL,
    notable_episodes_json TEXT NOT NULL,
    reusable_assets_json TEXT NOT NULL,
    topic_tags_json TEXT NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES articles(doc_id) ON DELETE CASCADE
);

-- 3. 추출된 이미지/도표 에셋 메타 테이블
CREATE TABLE IF NOT EXISTS article_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    page_no INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    caption TEXT DEFAULT '',
    width INTEGER,
    height INTEGER,
    FOREIGN KEY (doc_id) REFERENCES articles(doc_id) ON DELETE CASCADE
);

-- 4. 초고속 전문 검색을 위한 FTS5 가상 테이블 (unicode61 토크나이저 사용)
CREATE VIRTUAL TABLE IF NOT EXISTS metadata_fts USING fts5(
    doc_id UNINDEXED,
    title,
    primary_category,
    target_audience,
    core_problem,
    reframing_logic,
    core_thesis,
    solution_framework,
    notable_episodes,
    topic_tags,
    asset_captions,
    tokenize = 'unicode61 remove_diacritics 2'
);

-- 5. [v2.0 신규] 파이프라인 백그라운드 작업 및 실시간 진행률 모니터링 테이블
CREATE TABLE IF NOT EXISTS pipeline_jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RUNNING',
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    current_doc_id TEXT DEFAULT '',
    log_summary TEXT DEFAULT '',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 6. [v2.0 신규] 생성된 초안 및 사용자가 수정 확정한 '나의 결과물' 관리 테이블
CREATE TABLE IF NOT EXISTS drafts_and_creations (
    creation_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    direction TEXT DEFAULT '',
    target_archetype TEXT DEFAULT '',
    seed_doc_ids_json TEXT NOT NULL,
    blueprint_json TEXT NOT NULL,
    distilled_sheets_json TEXT NOT NULL,
    ai_draft_text TEXT NOT NULL,
    user_final_text TEXT DEFAULT '',
    custom_notes TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'DRAFT',
    used_for_style_learning INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalized_at TIMESTAMP
);

-- 7. [v2.1 신규] 시맨틱 벡터 임베딩 저장 테이블
CREATE TABLE IF NOT EXISTS article_embeddings (
    doc_id TEXT PRIMARY KEY,
    embedding_json TEXT NOT NULL,
    model TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES articles(doc_id) ON DELETE CASCADE
);

-- 8. [v2.1 신규] LLM 비용, 토큰, 지연시간 모니터링 테이블
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    latency_ms REAL DEFAULT 0.0,
    estimated_cost_usd REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Optimization Indexes
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts_and_creations(status);
CREATE INDEX IF NOT EXISTS idx_drafts_learning ON drafts_and_creations(used_for_style_learning);
CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status ON pipeline_jobs(status);
CREATE INDEX IF NOT EXISTS idx_llm_usage_task ON llm_usage_logs(task_type, created_at);
"""


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Create a configured SQLite connection."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db(db_path: str | Path) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database transactions."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | Path) -> None:
    """Initialize database tables and FTS5 virtual tables."""
    conn = get_connection(db_path)
    try:
        conn.executescript(DDL_STATEMENTS)
        conn.commit()
    finally:
        conn.close()
