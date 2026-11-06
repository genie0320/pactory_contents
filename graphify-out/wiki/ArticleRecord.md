# ArticleRecord

> 40 nodes · cohesion 0.10

## Key Concepts

- **ArticleRecord** (35 connections) — `src/models.py`
- **ArticleMetadata** (30 connections) — `src/models.py`
- **BatchMetadataExtractor** (25 connections) — `src/extraction/batch_extractor.py`
- **ArticleStatus** (25 connections) — `src/models.py`
- **test_extraction.py** (24 connections) — `tests/test_extraction.py`
- **test_jobs_and_creations.py** (24 connections) — `tests/test_jobs_and_creations.py`
- **test_storage.py** (21 connections) — `tests/test_storage.py`
- **test_synthesizer_job_and_creation_recording()** (15 connections) — `tests/test_jobs_and_creations.py`
- **cmd_extract()** (13 connections) — `run.py`
- **test_batch_extractor_job_tracking()** (10 connections) — `tests/test_jobs_and_creations.py`
- **test_fts5_indexing_and_speed_criteria()** (9 connections) — `tests/test_storage.py`
- **BaseModel** (8 connections)
- **._row_to_article()** (8 connections) — `src/storage/repository.py`
- **.upsert_article()** (7 connections) — `src/storage/repository.py`
- **.get_pending_articles()** (6 connections) — `src/extraction/batch_extractor.py`
- **.process_article()** (6 connections) — `src/extraction/batch_extractor.py`
- **.run_sync()** (6 connections) — `src/extraction/batch_extractor.py`
- **.get_article_by_hash()** (6 connections) — `src/storage/repository.py`
- **.process_article_sync()** (5 connections) — `src/extraction/batch_extractor.py`
- **.run()** (5 connections) — `src/extraction/batch_extractor.py`
- **test_fault_tolerant_checkpointing_resumption()** (4 connections) — `tests/test_extraction.py`
- **test_structured_metadata_extraction()** (3 connections) — `tests/test_extraction.py`
- **test_article_crud()** (3 connections) — `tests/test_storage.py`
- **Row** (1 connections)
- **Asynchronously extract structured ArticleMetadata with checkpoint resumption.** (1 connections) — `run.py`
- *... and 15 more nodes in this community*

## Relationships

- [llm_client.py](llm_client.py.md) (41 shared connections)
- [ArticleArchetype](ArticleArchetype.md) (28 shared connections)
- [AppConfig](AppConfig.md) (25 shared connections)
- [StorageRepository](StorageRepository.md) (17 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (14 shared connections)
- [get_db](get_db.md) (6 shared connections)
- [LLMClient](LLMClient.md) (5 shared connections)
- [test_pipeline_job_lifecycle](test_pipeline_job_lifecycle.md) (4 shared connections)
- [StyleLearner](StyleLearner.md) (3 shared connections)
- [.get_article](get_article.md) (3 shared connections)
- [.semaphore](semaphore.md) (2 shared connections)
- [.select_complementary_seeds](select_complementary_seeds.md) (2 shared connections)

## Source Files

- `run.py`
- `src/extraction/batch_extractor.py`
- `src/models.py`
- `src/storage/repository.py`
- `tests/test_extraction.py`
- `tests/test_jobs_and_creations.py`
- `tests/test_storage.py`

## Audit Trail

- EXTRACTED: 189 (80%)
- INFERRED: 46 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*