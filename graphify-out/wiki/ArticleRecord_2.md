# ArticleRecord

> God node · 35 connections · `src/models.py`

**Community:** [ArticleRecord](ArticleRecord.md)

## Connections by Relation

### calls
- test_synthesizer_job_and_creation_recording() `EXTRACTED`
- test_batch_extractor_job_tracking() `EXTRACTED`
- test_fts5_indexing_and_speed_criteria() `EXTRACTED`
- test_fault_tolerant_checkpointing_resumption() `EXTRACTED`
- test_structured_metadata_extraction() `EXTRACTED`
- test_article_crud() `EXTRACTED`
- test_visual_assets_and_manifest() `EXTRACTED`

### contains
- models.py `EXTRACTED`

### imports
- repository.py `EXTRACTED`
- test_style_learner.py `EXTRACTED`
- scanner.py `EXTRACTED`
- retriever.py `EXTRACTED`
- test_extraction.py `EXTRACTED`
- test_jobs_and_creations.py `EXTRACTED`
- batch_extractor.py `EXTRACTED`
- test_retriever.py `EXTRACTED`
- test_storage.py `EXTRACTED`

### inherits
- BaseModel `EXTRACTED`

### references
- .get_article() `EXTRACTED`
- .process_file() `EXTRACTED`
- .search_candidates() `EXTRACTED`
- .scan_inbox() `EXTRACTED`
- .list_articles() `EXTRACTED`
- ._row_to_article() `EXTRACTED`
- .upsert_article() `EXTRACTED`
- .get_pending_articles() `EXTRACTED`
- .get_article_by_hash() `EXTRACTED`
- .process_article() `EXTRACTED`
- .get_article_by_title() `EXTRACTED`
- .process_article_sync() `EXTRACTED`

### uses
- [StorageRepository](StorageRepository.md) `INFERRED`
- SeedRetriever `INFERRED`
- BatchMetadataExtractor `INFERRED`
- IngestionScanner `INFERRED`
- populated_retriever() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*