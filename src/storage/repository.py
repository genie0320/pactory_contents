"""Repository for articles, metadata, and asset storage operations."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.models import (
    ArticleMetadata,
    ArticleRecord,
    ArticleStatus,
    VisualAssetItem,
    VisualAssetManifest,
)
from src.storage.db import get_db, init_db


class StorageRepository:
    """Manages SQLite database records and filesystem assets."""

    def __init__(self, db_path: str | Path, processed_dir: str | Path | None = None):
        self.db_path = Path(db_path)
        self.processed_dir = Path(processed_dir) if processed_dir else self.db_path.parent.parent / "processed"
        self.texts_dir = self.processed_dir / "texts"
        self.metadata_dir = self.processed_dir / "metadata"
        self.assets_dir = self.processed_dir / "assets"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.texts_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        init_db(self.db_path)

    # -------------------------------------------------------------
    # 1. Article Registry (articles table)
    # -------------------------------------------------------------
    def upsert_article(self, article: ArticleRecord) -> None:
        """Insert or update article record in articles table."""
        sql = """
        INSERT INTO articles (
            doc_id, title, author, published_date, source_format,
            original_path, processed_text_path, assets_dir_path,
            content_hash, char_count, image_count, status, error_msg,
            ingested_at, indexed_at
        ) VALUES (
            :doc_id, :title, :author, :published_date, :source_format,
            :original_path, :processed_text_path, :assets_dir_path,
            :content_hash, :char_count, :image_count, :status, :error_msg,
            COALESCE(:ingested_at, CURRENT_TIMESTAMP), :indexed_at
        )
        ON CONFLICT(doc_id) DO UPDATE SET
            title=excluded.title,
            author=excluded.author,
            published_date=excluded.published_date,
            source_format=excluded.source_format,
            original_path=excluded.original_path,
            processed_text_path=excluded.processed_text_path,
            assets_dir_path=excluded.assets_dir_path,
            content_hash=excluded.content_hash,
            char_count=excluded.char_count,
            image_count=excluded.image_count,
            status=excluded.status,
            error_msg=excluded.error_msg,
            indexed_at=excluded.indexed_at
        """
        params = {
            "doc_id": article.doc_id,
            "title": article.title,
            "author": article.author,
            "published_date": article.published_date,
            "source_format": article.source_format,
            "original_path": str(article.original_path),
            "processed_text_path": str(article.processed_text_path),
            "assets_dir_path": str(article.assets_dir_path),
            "content_hash": article.content_hash,
            "char_count": article.char_count,
            "image_count": article.image_count,
            "status": article.status.value if isinstance(article.status, ArticleStatus) else article.status,
            "error_msg": article.error_msg,
            "ingested_at": article.ingested_at.isoformat() if article.ingested_at else None,
            "indexed_at": article.indexed_at.isoformat() if article.indexed_at else None,
        }
        with get_db(self.db_path) as conn:
            conn.execute(sql, params)

    def get_article(self, doc_id: str) -> ArticleRecord | None:
        """Fetch article by doc_id."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM articles WHERE doc_id = ?", (doc_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_article(row)

    def get_article_by_hash(self, content_hash: str) -> ArticleRecord | None:
        """Fetch article by content hash."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM articles WHERE content_hash = ?", (content_hash,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_article(row)

    def get_article_by_title(self, title: str) -> ArticleRecord | None:
        """Fetch article by exact title."""
        if not title:
            return None
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM articles WHERE title = ?", (title.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_article(row)

    def list_articles(
        self,
        status: str | ArticleStatus | None = None,
        limit: int | None = None,
    ) -> list[ArticleRecord]:
        """List articles, optionally filtered by status and limited."""
        query = "SELECT * FROM articles"
        params: list[Any] = []
        if status:
            val = status.value if isinstance(status, ArticleStatus) else status
            query += " WHERE status = ?"
            params.append(val)
        query += " ORDER BY ingested_at DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with get_db(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_article(r) for r in cursor.fetchall()]

    def update_article_status(self, doc_id: str, status: ArticleStatus, error_msg: str = "") -> None:
        """Update processing status of an article."""
        indexed_at = datetime.now(UTC).isoformat() if status == ArticleStatus.INDEXED else None
        sql = """
        UPDATE articles
        SET status = ?, error_msg = ?, indexed_at = COALESCE(?, indexed_at)
        WHERE doc_id = ?
        """
        with get_db(self.db_path) as conn:
            conn.execute(sql, (status.value, error_msg, indexed_at, doc_id))

    def _row_to_article(self, row: sqlite3.Row) -> ArticleRecord:
        return ArticleRecord(
            doc_id=row["doc_id"],
            title=row["title"],
            author=row["author"] or "",
            published_date=row["published_date"] or "",
            source_format=row["source_format"],
            original_path=row["original_path"],
            processed_text_path=row["processed_text_path"],
            assets_dir_path=row["assets_dir_path"] or "",
            content_hash=row["content_hash"],
            char_count=row["char_count"],
            image_count=row["image_count"],
            status=ArticleStatus(row["status"]),
            error_msg=row["error_msg"] or "",
            ingested_at=datetime.fromisoformat(row["ingested_at"]) if row["ingested_at"] else None,
            indexed_at=datetime.fromisoformat(row["indexed_at"]) if row["indexed_at"] else None,
        )

    def delete_article(self, doc_id: str, delete_files: bool = True) -> bool:
        """Delete an article and its related metadata, assets, and FTS index."""
        art = self.get_article(doc_id)
        if not art:
            return False

        with get_db(self.db_path) as conn:
            conn.execute("DELETE FROM metadata_fts WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM article_assets WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM article_metadata WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM articles WHERE doc_id = ?", (doc_id,))

        if delete_files:
            p_text = self.texts_dir / f"{doc_id}.md"
            if p_text.exists():
                try:
                    p_text.unlink()
                except Exception:
                    pass
            p_meta = self.metadata_dir / f"{doc_id}.json"
            if p_meta.exists():
                try:
                    p_meta.unlink()
                except Exception:
                    pass
            p_assets = self.assets_dir / doc_id
            if p_assets.exists() and p_assets.is_dir():
                import shutil
                try:
                    shutil.rmtree(p_assets, ignore_errors=True)
                except Exception:
                    pass

        return True

    # -------------------------------------------------------------
    # 2. Text and File Management
    # -------------------------------------------------------------
    def save_processed_text(self, doc_id: str, content: str) -> Path:
        """Save cleaned markdown text to data/processed/texts/{doc_id}.md."""
        file_path = self.texts_dir / f"{doc_id}.md"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def get_processed_text(self, doc_id: str) -> str:
        """Read cleaned text for doc_id."""
        file_path = self.texts_dir / f"{doc_id}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Processed text file not found: {file_path}")
        return file_path.read_text(encoding="utf-8")

    # -------------------------------------------------------------
    # 3. Visual Assets (article_assets table & manifest.json)
    # -------------------------------------------------------------
    def save_visual_assets(self, doc_id: str, assets: list[VisualAssetItem]) -> Path:
        """Save visual assets to article_assets table and manifest.json."""
        doc_asset_dir = self.assets_dir / doc_id
        doc_asset_dir.mkdir(parents=True, exist_ok=True)

        manifest = VisualAssetManifest(doc_id=doc_id, assets=assets)
        manifest_path = doc_asset_dir / "manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        with get_db(self.db_path) as conn:
            conn.execute("DELETE FROM article_assets WHERE doc_id = ?", (doc_id,))
            for item in assets:
                conn.execute(
                    """
                    INSERT INTO article_assets (doc_id, asset_id, page_no, file_path, caption, width, height)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (doc_id, item.asset_id, item.page_no, str(item.file_path), item.caption, item.width, item.height),
                )
            conn.execute("UPDATE articles SET image_count = ? WHERE doc_id = ?", (len(assets), doc_id))

        return manifest_path

    def get_visual_assets(self, doc_id: str) -> list[VisualAssetItem]:
        """Fetch visual assets for doc_id."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT asset_id, page_no, file_path, caption, width, height FROM article_assets WHERE doc_id = ? ORDER BY page_no, asset_id",
                (doc_id,),
            )
            return [
                VisualAssetItem(
                    asset_id=r["asset_id"],
                    page_no=r["page_no"],
                    file_path=r["file_path"],
                    caption=r["caption"] or "",
                    width=r["width"],
                    height=r["height"],
                )
                for r in cursor.fetchall()
            ]

    # -------------------------------------------------------------
    # 4. Metadata & FTS5 Indexing
    # -------------------------------------------------------------
    def save_article_metadata(
        self,
        doc_id: str,
        metadata: ArticleMetadata,
        title: str | None = None,
        asset_captions: str = "",
    ) -> Path:
        """
        Save metadata atomically:
        1. Write data/processed/metadata/{doc_id}.json
        2. Insert or replace into article_metadata table
        3. Synchronize metadata_fts virtual table
        4. Update articles.status = 'INDEXED'
        """
        # 1. Write individual JSON backup
        json_path = self.metadata_dir / f"{doc_id}.json"
        json_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

        # 2. Get article title if not provided
        if not title:
            article = self.get_article(doc_id)
            title = article.title if article else doc_id

        # Format FTS searchable texts
        solution_fw_text = " | ".join(metadata.solution_framework)
        notable_episodes_text = " | ".join(metadata.notable_episodes)
        topic_tags_text = " ".join(metadata.topic_tags)

        # Asset captions from DB if not passed
        if not asset_captions:
            assets = self.get_visual_assets(doc_id)
            asset_captions = " ".join(a.caption for a in assets if a.caption)

        with get_db(self.db_path) as conn:
            # Upsert article_metadata
            conn.execute(
                """
                INSERT INTO article_metadata (
                    doc_id, primary_category, article_archetype, target_audience,
                    core_problem, reframing_logic, core_thesis, hook_strategy,
                    solution_framework_json, notable_episodes_json, reusable_assets_json, topic_tags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    primary_category=excluded.primary_category,
                    article_archetype=excluded.article_archetype,
                    target_audience=excluded.target_audience,
                    core_problem=excluded.core_problem,
                    reframing_logic=excluded.reframing_logic,
                    core_thesis=excluded.core_thesis,
                    hook_strategy=excluded.hook_strategy,
                    solution_framework_json=excluded.solution_framework_json,
                    notable_episodes_json=excluded.notable_episodes_json,
                    reusable_assets_json=excluded.reusable_assets_json,
                    topic_tags_json=excluded.topic_tags_json
                """,
                (
                    doc_id,
                    metadata.primary_category,
                    metadata.article_archetype.value,
                    metadata.target_audience,
                    metadata.core_problem,
                    metadata.reframing_logic,
                    metadata.core_thesis,
                    metadata.hook_strategy,
                    json.dumps(metadata.solution_framework, ensure_ascii=False),
                    json.dumps(metadata.notable_episodes, ensure_ascii=False),
                    json.dumps([a.value for a in metadata.reusable_asset_types], ensure_ascii=False),
                    json.dumps(metadata.topic_tags, ensure_ascii=False),
                ),
            )

            # Sync FTS5 virtual table
            conn.execute("DELETE FROM metadata_fts WHERE doc_id = ?", (doc_id,))
            conn.execute(
                """
                INSERT INTO metadata_fts (
                    doc_id, title, primary_category, target_audience, core_problem,
                    reframing_logic, core_thesis, solution_framework, notable_episodes,
                    topic_tags, asset_captions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    title,
                    metadata.primary_category,
                    metadata.target_audience,
                    metadata.core_problem,
                    metadata.reframing_logic,
                    metadata.core_thesis,
                    solution_fw_text,
                    notable_episodes_text,
                    topic_tags_text,
                    asset_captions,
                ),
            )

            # Mark indexed
            now_iso = datetime.now(UTC).isoformat()
            conn.execute(
                "UPDATE articles SET status = 'INDEXED', indexed_at = ? WHERE doc_id = ?",
                (now_iso, doc_id),
            )

        return json_path

    def get_article_metadata(self, doc_id: str) -> ArticleMetadata | None:
        """Retrieve ArticleMetadata from SQLite or JSON file fallback."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM article_metadata WHERE doc_id = ?", (doc_id,))
            row = cursor.fetchone()
            if row:
                return ArticleMetadata(
                    target_audience=row["target_audience"],
                    core_problem=row["core_problem"],
                    reframing_logic=row["reframing_logic"],
                    core_thesis=row["core_thesis"],
                    article_archetype=row["article_archetype"],
                    hook_strategy=row["hook_strategy"],
                    solution_framework=json.loads(row["solution_framework_json"]),
                    notable_episodes=json.loads(row["notable_episodes_json"]),
                    reusable_asset_types=json.loads(row["reusable_assets_json"]),
                    primary_category=row["primary_category"],
                    topic_tags=json.loads(row["topic_tags_json"]),
                )

        json_path = self.metadata_dir / f"{doc_id}.json"
        if json_path.exists():
            return ArticleMetadata.model_validate_json(json_path.read_text(encoding="utf-8"))

        return None

    # -------------------------------------------------------------
    # 5. Pipeline Jobs Management (pipeline_jobs table)
    # -------------------------------------------------------------
    def create_job(self, job_id: str, job_type: str, total_items: int = 0) -> str:
        """Create a new pipeline job record in RUNNING status."""
        now_iso = datetime.now(UTC).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO pipeline_jobs (
                    job_id, job_type, status, total_items, processed_items, failed_items,
                    current_doc_id, log_summary, started_at, updated_at
                ) VALUES (?, ?, 'RUNNING', ?, 0, 0, '', '', ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    job_type=excluded.job_type,
                    status='RUNNING',
                    total_items=excluded.total_items,
                    updated_at=excluded.updated_at
                """,
                (job_id, job_type, total_items, now_iso, now_iso),
            )
        return job_id

    def update_job_progress(
        self,
        job_id: str,
        processed_delta: int = 0,
        failed_delta: int = 0,
        total_items: int | None = None,
        current_doc_id: str | None = None,
        log_summary: str | None = None,
        status: str | None = None,
    ) -> None:
        """Increment progress and update status of a pipeline job."""
        now_iso = datetime.now(UTC).isoformat()
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT processed_items, failed_items, total_items, log_summary FROM pipeline_jobs WHERE job_id = ?",
                (job_id,),
            )
            row = cursor.fetchone()
            if not row:
                return

            new_processed = row["processed_items"] + processed_delta
            new_failed = row["failed_items"] + failed_delta
            new_total = total_items if total_items is not None else row["total_items"]
            new_summary = log_summary if log_summary is not None else row["log_summary"]

            sql = """
            UPDATE pipeline_jobs
            SET processed_items = ?,
                failed_items = ?,
                total_items = ?,
                current_doc_id = COALESCE(?, current_doc_id),
                log_summary = ?,
                status = COALESCE(?, status),
                updated_at = ?
            WHERE job_id = ?
            """
            conn.execute(
                sql,
                (new_processed, new_failed, new_total, current_doc_id, new_summary, status, now_iso, job_id),
            )

    def complete_job(
        self,
        job_id: str,
        status: str = "COMPLETED",
        log_summary: str | None = None,
    ) -> None:
        """Mark a job as COMPLETED or FAILED."""
        now_iso = datetime.now(UTC).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                UPDATE pipeline_jobs
                SET status = ?,
                    completed_at = ?,
                    updated_at = ?,
                    log_summary = COALESCE(?, log_summary)
                WHERE job_id = ?
                """,
                (status, now_iso, now_iso, log_summary, job_id),
            )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Fetch job record by job_id as a dictionary."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM pipeline_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent pipeline jobs."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM pipeline_jobs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def delete_job(self, job_id: str) -> bool:
        """Delete a single job log."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM pipeline_jobs WHERE job_id = ?", (job_id,))
            return cursor.rowcount > 0

    def delete_all_jobs(self) -> int:
        """Delete all job logs."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM pipeline_jobs")
            return cursor.rowcount

    def delete_creation(self, creation_id: str) -> bool:
        """Delete a draft creation."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM drafts_and_creations WHERE creation_id = ?", (creation_id,))
            return cursor.rowcount > 0

    # -------------------------------------------------------------
    # 6. Drafts and Creations Management (drafts_and_creations table)
    # -------------------------------------------------------------
    def save_draft_creation(
        self,
        creation_id: str,
        topic: str,
        direction: str,
        target_archetype: str,
        seed_doc_ids: list[str],
        blueprint_json: str,
        distilled_sheets_json: str,
        ai_draft_text: str,
        status: str = "DRAFT",
    ) -> str:
        """Save a generated draft into drafts_and_creations table."""
        now_iso = datetime.now(UTC).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO drafts_and_creations (
                    creation_id, topic, direction, target_archetype,
                    seed_doc_ids_json, blueprint_json, distilled_sheets_json,
                    ai_draft_text, user_final_text, custom_notes,
                    status, used_for_style_learning, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, 0, ?)
                ON CONFLICT(creation_id) DO UPDATE SET
                    topic=excluded.topic,
                    direction=excluded.direction,
                    target_archetype=excluded.target_archetype,
                    seed_doc_ids_json=excluded.seed_doc_ids_json,
                    blueprint_json=excluded.blueprint_json,
                    distilled_sheets_json=excluded.distilled_sheets_json,
                    ai_draft_text=excluded.ai_draft_text,
                    status=excluded.status
                """,
                (
                    creation_id,
                    topic,
                    direction,
                    target_archetype,
                    json.dumps(seed_doc_ids, ensure_ascii=False),
                    blueprint_json,
                    distilled_sheets_json,
                    ai_draft_text,
                    status,
                    now_iso,
                ),
            )
        return creation_id

    def update_creation_final(
        self,
        creation_id: str,
        user_final_text: str,
        custom_notes: str = "",
        status: str = "FINALIZED",
    ) -> None:
        """Update draft to FINALIZED with user modifications."""
        now_iso = datetime.now(UTC).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                UPDATE drafts_and_creations
                SET user_final_text = ?,
                    custom_notes = ?,
                    status = ?,
                    finalized_at = ?
                WHERE creation_id = ?
                """,
                (user_final_text, custom_notes, status, now_iso, creation_id),
            )

    def cleanup_older_drafts(self, topic: str, keep_creation_id: str) -> None:
        """Clean up duplicate older DRAFT records for the same topic upon finalization."""
        if not topic:
            return
        with get_db(self.db_path) as conn:
            conn.execute(
                "DELETE FROM drafts_and_creations WHERE topic = ? AND status = 'DRAFT' AND creation_id != ?",
                (topic, keep_creation_id),
            )

    def sync_creation_to_outputs(self, outputs_dir: Path, creation_id: str, topic: str, text: str) -> None:
        """Dual-write real-time synchronization between DB and filesystem output directory."""
        if not text:
            return
        try:
            outputs_dir.mkdir(parents=True, exist_ok=True)
            matched = list(outputs_dir.glob(f"{creation_id}*.md"))
            if not matched and "cr_" in creation_id:
                ts_part = creation_id.replace("cr_", "")
                matched = list(outputs_dir.glob(f"*{ts_part}*.md"))

            if matched:
                for target_file in matched:
                    target_file.write_text(text, encoding="utf-8")
            else:
                import re
                raw_topic = topic or "draft"
                safe_slug = re.sub(r"[^\w\s-]", "", raw_topic.lower()).strip()
                safe_slug = re.sub(r"[-\s]+", "_", safe_slug)[:40] or "final"
                target_file = outputs_dir / f"{creation_id}_{safe_slug}.md"
                target_file.write_text(text, encoding="utf-8")
        except Exception:
            pass

    def get_creation(self, creation_id: str) -> dict[str, Any] | None:
        """Fetch a single creation record by creation_id."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM drafts_and_creations WHERE creation_id = ?",
                (creation_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["seed_doc_ids"] = json.loads(res["seed_doc_ids_json"]) if res.get("seed_doc_ids_json") else []
            return res

    def list_creations(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List creations, optionally filtered by status."""
        query = "SELECT * FROM drafts_and_creations"
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_db(self.db_path) as conn:
            cursor = conn.execute(query, params)
            results = []
            for r in cursor.fetchall():
                item = dict(r)
                item["seed_doc_ids"] = json.loads(item["seed_doc_ids_json"]) if item.get("seed_doc_ids_json") else []
                results.append(item)
            return results

    def get_recently_used_seed_ids(self, days: int = 7) -> set[str]:
        """
        Fetch distinct seed doc_ids adopted in creations generated within the last N days.
        Used to apply cooldown penalty to prevent seed fatigue and monotonous recommendations.
        """
        from datetime import timedelta
        cutoff_iso = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        recent_ids: set[str] = set()

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT seed_doc_ids_json FROM drafts_and_creations
                WHERE created_at >= ? AND seed_doc_ids_json IS NOT NULL
                """,
                (cutoff_iso,),
            )
            for row in cursor.fetchall():
                raw = row["seed_doc_ids_json"]
                if raw:
                    try:
                        ids = json.loads(raw)
                        if isinstance(ids, list):
                            recent_ids.update(str(i) for i in ids if i)
                    except Exception:
                        pass
        return recent_ids

    def get_finalized_creations_for_learning(
        self,
        min_count: int = 1,
        include_already_used: bool = False,
        window_size: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Fetch finalized creations with user_final_text for persona style learning.
        Supports sliding window (up to window_size most recent creations) and force learning (min_count >= 1).
        """
        with get_db(self.db_path) as conn:
            # 1. First, check strictly unlearned items
            cursor = conn.execute(
                """
                SELECT * FROM drafts_and_creations
                WHERE status = 'FINALIZED'
                  AND user_final_text IS NOT NULL
                  AND LENGTH(TRIM(user_final_text)) > 0
                  AND used_for_style_learning = 0
                ORDER BY finalized_at ASC
                """
            )
            items = []
            for r in cursor.fetchall():
                d = dict(r)
                d["seed_doc_ids"] = json.loads(d["seed_doc_ids_json"]) if d.get("seed_doc_ids_json") else []
                items.append(d)

            if len(items) >= min_count:
                return items[:window_size]

            # 2. Sliding window fallback: If unlearned items are below min_count and include_already_used is True,
            # gather the most recent finalized creations so style evolves dynamically.
            if include_already_used:
                cursor_all = conn.execute(
                    """
                    SELECT * FROM drafts_and_creations
                    WHERE status = 'FINALIZED'
                      AND user_final_text IS NOT NULL
                      AND LENGTH(TRIM(user_final_text)) > 0
                    ORDER BY COALESCE(finalized_at, created_at) DESC
                    LIMIT ?
                    """,
                    (window_size,),
                )
                all_items = []
                for r in cursor_all.fetchall():
                    d = dict(r)
                    d["seed_doc_ids"] = json.loads(d["seed_doc_ids_json"]) if d.get("seed_doc_ids_json") else []
                    all_items.append(d)

                if len(all_items) >= min_count:
                    return all_items

            return items if len(items) >= min_count else []

    def mark_creations_used_for_style(self, creation_ids: list[str]) -> None:
        """Mark creation records as used_for_style_learning = 1."""
        if not creation_ids:
            return
        placeholders = ",".join("?" for _ in creation_ids)
        with get_db(self.db_path) as conn:
            conn.execute(
                f"UPDATE drafts_and_creations SET used_for_style_learning = 1 WHERE creation_id IN ({placeholders})",
                creation_ids,
            )

    # -------------------------------------------------------------
    # 7. Dense Vector Embeddings (article_embeddings table)
    # -------------------------------------------------------------
    def upsert_article_embedding(self, doc_id: str, embedding: list[float], model: str = "text-embedding-004") -> None:
        """Store or update dense vector embedding for an article."""
        now_iso = datetime.now(UTC).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO article_embeddings (doc_id, embedding_json, model, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    embedding_json = excluded.embedding_json,
                    model = excluded.model,
                    updated_at = excluded.updated_at
                """,
                (doc_id, json.dumps(embedding), model, now_iso),
            )

    def get_article_embedding(self, doc_id: str) -> list[float] | None:
        """Retrieve embedding vector for a single article."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT embedding_json FROM article_embeddings WHERE doc_id = ?", (doc_id,))
            row = cursor.fetchone()
            if row and row["embedding_json"]:
                return json.loads(row["embedding_json"])
        return None

    def get_all_embeddings(self) -> dict[str, list[float]]:
        """Retrieve all stored embedding vectors as a map of doc_id -> vector."""
        res: dict[str, list[float]] = {}
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT doc_id, embedding_json FROM article_embeddings")
            for row in cursor.fetchall():
                try:
                    res[row["doc_id"]] = json.loads(row["embedding_json"])
                except Exception:
                    continue
        return res

    # -------------------------------------------------------------
    # 8. Observability & LLM Usage Logging (llm_usage_logs table)
    # -------------------------------------------------------------
    def log_llm_usage(
        self,
        task_type: str,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        """Log token count, latency, and cost for an LLM invocation."""
        now_iso = datetime.now(UTC).isoformat()
        total_tokens = prompt_tokens + completion_tokens
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO llm_usage_logs (
                    task_type, provider, model, prompt_tokens,
                    completion_tokens, total_tokens, latency_ms,
                    estimated_cost_usd, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_type, provider, model, prompt_tokens, completion_tokens, total_tokens, latency_ms, estimated_cost_usd, now_iso),
            )

    def get_observability_stats(self) -> dict[str, Any]:
        """Aggregate total tokens, invocations, average latency, and estimated cost."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_calls,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                    COALESCE(AVG(latency_ms), 0.0) as avg_latency_ms,
                    COALESCE(SUM(estimated_cost_usd), 0.0) as total_cost_usd
                FROM llm_usage_logs
                """
            )
            row = cursor.fetchone()
            if row:
                return {
                    "total_calls": row["total_calls"],
                    "total_tokens": row["total_tokens"],
                    "prompt_tokens": row["prompt_tokens"],
                    "completion_tokens": row["completion_tokens"],
                    "avg_latency_ms": round(float(row["avg_latency_ms"]), 1),
                    "total_cost_usd": round(float(row["total_cost_usd"]), 5),
                }
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "avg_latency_ms": 0.0,
                "total_cost_usd": 0.0,
            }
