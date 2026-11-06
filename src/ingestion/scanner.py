"""Scanner and ingestion pipeline: scans inbox, checks duplicates, normalizes, and routes files."""

import hashlib
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from src.config import AppConfig, load_config
from src.ingestion.pdf_processor import PDFProcessor
from src.ingestion.text_normalizer import normalize_markdown
from src.models import ArticleRecord, ArticleStatus, VisualAssetItem
from src.storage.repository import StorageRepository


class IngestionScanner:
    """Scans inbox folder, checks SHA-256 hash, and routes files to processed and archive."""

    def __init__(self, config: Optional[AppConfig] = None, repo: Optional[StorageRepository] = None):
        self.config = config or load_config()
        self.config.ensure_directories()
        self.repo = repo or StorageRepository(
            db_path=self.config.paths.db_path,
            processed_dir=self.config.paths.processed_dir,
        )
        self.pdf_processor = PDFProcessor(image_filter=self.config.image_filter)

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def parse_filename(filename: str) -> Tuple[Optional[str], str]:
        """
        Extract doc_id and initial title from filename.
        Example: '8219_그때 그거 어디서 정했죠.pdf' -> ('8219', '그때 그거 어디서 정했죠')
        """
        match = re.match(r"^(\d+)_(.+)\.(pdf|md|txt)$", filename, flags=re.IGNORECASE)
        if match:
            doc_id = match.group(1)
            title = match.group(2).strip()
            return doc_id, title

        # Fallback when no number prefix
        stem = Path(filename).stem
        return None, stem

    def scan_inbox(
        self,
        inbox_dir: Optional[Path] = None,
        force: bool = False,
        move_archive: bool = False,
        job_id: Optional[str] = None,
    ) -> List[ArticleRecord]:
        """
        Scan inbox directory for .pdf, .md, and .txt files.
        Processes each file, writes clean texts and assets, and updates DB.
        """
        target_dir = Path(inbox_dir) if inbox_dir else self.config.paths.inbox_dir
        if not target_dir.exists():
            return []

        processed_records: List[ArticleRecord] = []
        supported_extensions = {".pdf", ".md", ".txt"}
        candidate_files = [p for p in target_dir.iterdir() if p.is_file() and p.suffix.lower() in supported_extensions]

        if not candidate_files:
            return []

        if not job_id:
            job_id = f"ingest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            self.repo.create_job(job_id=job_id, job_type="INGESTION", total_items=len(candidate_files))

        for file_path in candidate_files:
            try:
                record = self.process_file(file_path=file_path, force=force, move_archive=move_archive)
                if record:
                    processed_records.append(record)
                    self.repo.update_job_progress(
                        job_id=job_id,
                        processed_delta=1,
                        current_doc_id=record.doc_id,
                        log_summary=f"Ingested {file_path.name}",
                    )
                else:
                    self.repo.update_job_progress(
                        job_id=job_id,
                        failed_delta=1,
                        log_summary=f"Skipped {file_path.name}",
                    )
            except Exception as exc:
                self.repo.update_job_progress(
                    job_id=job_id,
                    failed_delta=1,
                    log_summary=f"Error {file_path.name}: {exc}",
                )

        self.repo.complete_job(
            job_id=job_id,
            status="COMPLETED",
            log_summary=f"Ingested {len(processed_records)}/{len(candidate_files)} files.",
        )

        return processed_records

    def process_file(
        self,
        file_path: Path,
        force: bool = False,
        move_archive: bool = False,
    ) -> Optional[ArticleRecord]:
        """Process a single file through the ingestion pipeline."""
        content_hash = self.compute_sha256(file_path)

        # Check duplication in database
        existing = self.repo.get_article_by_hash(content_hash)
        if existing and not force:
            if move_archive:
                try:
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass
            return existing

        filename = file_path.name
        doc_id, extracted_title = self.parse_filename(filename)
        if not doc_id:
            # Fallback to first 8 chars of SHA-256
            doc_id = content_hash[:8]

        ext = file_path.suffix.lower().lstrip(".")
        author = ""
        published_date = ""
        visual_assets: List[VisualAssetItem] = []
        cleaned_text = ""

        # Assets destination directory
        doc_assets_dir = self.config.paths.assets_dir / doc_id

        if ext == "pdf":
            cleaned_text, title_candidate, author, published_date, visual_assets = self.pdf_processor.process_pdf(
                pdf_path=file_path,
                doc_id=doc_id,
                assets_output_dir=doc_assets_dir,
            )
            title = extracted_title if extracted_title else title_candidate
        else:
            raw_text = file_path.read_text(encoding="utf-8", errors="replace")
            cleaned_text, title_candidate, author, published_date = normalize_markdown(
                raw_content=raw_text,
                fallback_title=extracted_title or filename,
            )
            title = extracted_title if extracted_title else title_candidate

        # Save processed markdown text
        saved_text_path = self.repo.save_processed_text(doc_id=doc_id, content=cleaned_text)

        # Route original file to archive
        archive_dest = self.config.paths.archive_dir / f"{doc_id}_{filename}"
        if move_archive:
            shutil.move(str(file_path), str(archive_dest))
            stored_orig_path = str(archive_dest)
        else:
            # Keep original in inbox, but copy to archive for backup
            shutil.copy2(str(file_path), str(archive_dest))
            stored_orig_path = str(archive_dest)

        char_count = len(cleaned_text)

        article = ArticleRecord(
            doc_id=doc_id,
            title=title,
            author=author,
            published_date=published_date,
            source_format=ext,
            original_path=stored_orig_path,
            processed_text_path=str(saved_text_path),
            assets_dir_path=str(doc_assets_dir) if visual_assets else "",
            content_hash=content_hash,
            char_count=char_count,
            image_count=len(visual_assets),
            status=ArticleStatus.INGESTED,
        )

        self.repo.upsert_article(article)

        # Save visual assets if any (after article record is inserted for FK constraint)
        if visual_assets:
            self.repo.save_visual_assets(doc_id=doc_id, assets=visual_assets)

        return article
