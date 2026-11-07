"""Asynchronous fault-tolerant batch metadata extractor with checkpointing."""

import asyncio
from datetime import UTC, datetime

from src.config import AppConfig, load_config
from src.extraction.llm_client import LLMClient
from src.extraction.prompts import (
    METADATA_EXTRACTION_SYSTEM_PROMPT,
    METADATA_EXTRACTION_USER_PROMPT,
)
from src.models import ArticleMetadata, ArticleRecord, ArticleStatus
from src.storage.repository import StorageRepository


class BatchMetadataExtractor:
    """Extracts ArticleMetadata asynchronously with checkpointing and semaphore control."""

    def __init__(
        self,
        config: AppConfig | None = None,
        repo: StorageRepository | None = None,
        llm_client: LLMClient | None = None,
        concurrency: int | None = None,
    ):
        self.config = config or load_config()
        self.repo = repo or StorageRepository(
            db_path=self.config.paths.db_path,
            processed_dir=self.config.paths.processed_dir,
        )
        self.concurrency = concurrency or self.config.extraction.concurrency
        self._semaphore: asyncio.Semaphore | None = None
        self.llm_client = llm_client or LLMClient(
            provider=self.config.extraction.default_provider,
            model=self.config.extraction.default_model,
        )

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """Lazy initialized semaphore bound to the active running event loop."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.concurrency)
        return self._semaphore

    def get_pending_articles(self) -> list[ArticleRecord]:
        """
        Checkpoint lookup:
        Fetch only articles that are not yet INDEXED (i.e. status INGESTED or FAILED).
        """
        all_articles = self.repo.list_articles()
        pending = [
            a for a in all_articles if a.status in (ArticleStatus.INGESTED, ArticleStatus.FAILED)
        ]
        return pending

    async def process_article(
        self,
        article: ArticleRecord,
        job_id: str | None = None,
    ) -> ArticleMetadata | None:
        """Process a single article with semaphore concurrency limit and immediate commit."""
        async with self.semaphore:
            doc_id = article.doc_id
            try:
                # Load processed text
                content = self.repo.get_processed_text(doc_id)
                # Cap content to around 15,000 chars to avoid unnecessary context overload
                sample_content = content[:15000]

                user_prompt = METADATA_EXTRACTION_USER_PROMPT.format(
                    title=f"[{doc_id}] {article.title}",
                    content=sample_content,
                )

                # LLM call with structured output
                metadata = await self.llm_client.extract_structured(
                    system_prompt=METADATA_EXTRACTION_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    schema=ArticleMetadata,
                    task_type="metadata_extraction",
                )

                # Immediate checkpoint commit:
                # 1. Write json, 2. DB upsert, 3. FTS sync, 4. status = INDEXED
                self.repo.save_article_metadata(
                    doc_id=doc_id,
                    metadata=metadata,
                    title=article.title,
                )

                if job_id:
                    self.repo.update_job_progress(
                        job_id=job_id,
                        processed_delta=1,
                        current_doc_id=doc_id,
                        log_summary=f"Indexed {doc_id}",
                    )

                return metadata

            except Exception as exc:
                self.repo.update_article_status(
                    doc_id=doc_id,
                    status=ArticleStatus.FAILED,
                    error_msg=str(exc),
                )
                if job_id:
                    self.repo.update_job_progress(
                        job_id=job_id,
                        failed_delta=1,
                        current_doc_id=doc_id,
                        log_summary=f"Failed {doc_id}: {exc}",
                    )
                return None

    def process_article_sync(
        self,
        article: ArticleRecord,
        job_id: str | None = None,
    ) -> ArticleMetadata | None:
        """Synchronous single-article extraction."""
        doc_id = article.doc_id
        try:
            content = self.repo.get_processed_text(doc_id)
            sample_content = content[:15000]

            user_prompt = METADATA_EXTRACTION_USER_PROMPT.format(
                title=f"[{doc_id}] {article.title}",
                content=sample_content,
            )

            metadata = self.llm_client.extract_structured_sync(
                system_prompt=METADATA_EXTRACTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema=ArticleMetadata,
            )

            self.repo.save_article_metadata(
                doc_id=doc_id,
                metadata=metadata,
                title=article.title,
            )

            if job_id:
                self.repo.update_job_progress(
                    job_id=job_id,
                    processed_delta=1,
                    current_doc_id=doc_id,
                    log_summary=f"Indexed {doc_id}",
                )

            return metadata
        except Exception as exc:
            self.repo.update_article_status(
                doc_id=doc_id,
                status=ArticleStatus.FAILED,
                error_msg=str(exc),
            )
            if job_id:
                self.repo.update_job_progress(
                    job_id=job_id,
                    failed_delta=1,
                    current_doc_id=doc_id,
                    log_summary=f"Failed {doc_id}: {exc}",
                )
            return None

    async def run(
        self,
        doc_ids: list[str] | None = None,
        max_items: int | None = None,
        job_id: str | None = None,
    ) -> list[str]:
        """
        Run extraction for pending articles.
        Returns list of newly indexed doc_ids.
        """
        self._semaphore = asyncio.Semaphore(self.concurrency)
        if doc_ids:
            pending = [self.repo.get_article(did) for did in doc_ids]
            pending = [a for a in pending if a is not None]
        else:
            pending = self.get_pending_articles()

        if max_items:
            pending = pending[:max_items]

        if not pending:
            return []

        if not job_id:
            job_id = f"extract_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        if not self.repo.get_job(job_id):
            self.repo.create_job(job_id=job_id, job_type="METADATA_EXTRACTION", total_items=len(pending))

        tasks = [self.process_article(article, job_id=job_id) for article in pending]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful_doc_ids = [
            article.doc_id for article, meta in zip(pending, results) if meta is not None
        ]

        if job_id:
            status = "COMPLETED" if len(successful_doc_ids) == len(pending) else "PARTIAL_SUCCESS"
            self.repo.complete_job(
                job_id=job_id,
                status=status,
                log_summary=f"Extracted {len(successful_doc_ids)}/{len(pending)} articles successfully.",
            )

        return successful_doc_ids

    def run_sync(
        self,
        doc_ids: list[str] | None = None,
        max_items: int | None = None,
        job_id: str | None = None,
    ) -> list[str]:
        """Synchronous run for pending articles with job tracking."""
        if doc_ids:
            pending = [self.repo.get_article(did) for did in doc_ids]
            pending = [a for a in pending if a is not None]
        else:
            pending = self.get_pending_articles()

        if max_items:
            pending = pending[:max_items]

        if not pending:
            return []

        if not job_id:
            job_id = f"extract_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        if not self.repo.get_job(job_id):
            self.repo.create_job(job_id=job_id, job_type="METADATA_EXTRACTION", total_items=len(pending))

        successful_doc_ids = []
        for article in pending:
            meta = self.process_article_sync(article, job_id=job_id)
            if meta is not None:
                successful_doc_ids.append(article.doc_id)

        if job_id:
            status = "COMPLETED" if len(successful_doc_ids) == len(pending) else "PARTIAL_SUCCESS"
            self.repo.complete_job(
                job_id=job_id,
                status=status,
                log_summary=f"Extracted {len(successful_doc_ids)}/{len(pending)} articles successfully.",
            )

        return successful_doc_ids
