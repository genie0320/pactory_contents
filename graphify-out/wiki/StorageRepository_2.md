# StorageRepository

> God node · 107 connections · `src/storage/repository.py`

**Community:** [StorageRepository](StorageRepository.md)

## Connections by Relation

### calls
- test_10_sample_articles_ingestion() `EXTRACTED`
- get_services() `EXTRACTED`
- get_services() `EXTRACTED`

### contains
- repository.py `EXTRACTED`

### imports
- legacy_streamlit_app.py `EXTRACTED`
- [routers/generator.py](routers-generator.py.md) `EXTRACTED`
- app.py `EXTRACTED`
- run.py `EXTRACTED`
- synthesizer.py `EXTRACTED`
- routers/editor.py `EXTRACTED`
- test_distiller.py `EXTRACTED`
- test_style_learner.py `EXTRACTED`
- [routers/inbox.py](routers-inbox.py.md) `EXTRACTED`
- routers/style.py `EXTRACTED`
- scanner.py `EXTRACTED`
- retriever.py `EXTRACTED`
- test_ingestion.py `EXTRACTED`
- test_synthesizer.py `EXTRACTED`
- test_extraction.py `EXTRACTED`
- test_jobs_and_creations.py `EXTRACTED`
- batch_extractor.py `EXTRACTED`
- test_retriever.py `EXTRACTED`
- test_storage.py `EXTRACTED`
- style_learner.py `EXTRACTED`
- *…and 2 more `imports` connection(s) not listed (lowest-degree first to go)*

### method
- .get_article() `EXTRACTED`
- .list_articles() `EXTRACTED`
- ._row_to_article() `EXTRACTED`
- .save_processed_text() `EXTRACTED`
- .save_article_metadata() `EXTRACTED`
- .get_creation() `EXTRACTED`
- .upsert_article() `EXTRACTED`
- .list_creations() `EXTRACTED`
- .save_visual_assets() `EXTRACTED`
- .get_job() `EXTRACTED`
- .list_jobs() `EXTRACTED`
- .save_draft_creation() `EXTRACTED`
- .get_article_by_hash() `EXTRACTED`
- .get_article_by_title() `EXTRACTED`
- .get_visual_assets() `EXTRACTED`
- .get_article_metadata() `EXTRACTED`
- .update_creation_final() `EXTRACTED`
- .get_finalized_creations_for_learning() `EXTRACTED`
- .get_observability_stats() `EXTRACTED`
- .update_article_status() `EXTRACTED`
- *…and 15 more `method` connection(s) not listed (lowest-degree first to go)*

### rationale_for
- Manages SQLite database records and filesystem assets. `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`

### uses
- [ArticleRecord](ArticleRecord.md) `INFERRED`
- [ArticleSynthesizer](ArticleSynthesizer.md) `INFERRED`
- SeedRetriever `INFERRED`
- ArticleMetadata `INFERRED`
- [StyleLearner](StyleLearner.md) `INFERRED`
- BatchMetadataExtractor `INFERRED`
- IngestionScanner `INFERRED`
- ArticleStatus `INFERRED`
- synthesize_draft() `INFERRED`
- [MaterialDistiller](MaterialDistiller.md) `INFERRED`
- distillation_env() `INFERRED`
- populated_retriever() `INFERRED`
- test_synthesizer_job_and_creation_recording() `INFERRED`
- VisualAssetItem `INFERRED`
- generate_blueprint() `INFERRED`
- scan_inbox() `INFERRED`
- synthesizer_env() `INFERRED`
- extraction_env() `INFERRED`
- style_env() `INFERRED`
- test_batch_extractor_job_tracking() `INFERRED`
- *…and 19 more `uses` connection(s) not listed (lowest-degree first to go)*

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*