# get_db

> 16 nodes · cohesion 0.14

## Key Concepts

- **get_db()** (36 connections) — `src/storage/db.py`
- **get_connection()** (13 connections) — `src/storage/db.py`
- **.delete_creation()** (4 connections) — `src/storage/repository.py`
- **.update_article_status()** (4 connections) — `src/storage/repository.py`
- **Path** (3 connections)
- **.get_article_embedding()** (3 connections) — `src/storage/repository.py`
- **.upsert_article_embedding()** (3 connections) — `src/storage/repository.py`
- **Connection** (2 connections)
- **.delete_all_jobs()** (2 connections) — `src/storage/repository.py`
- **test_init_db_creates_tables()** (2 connections) — `tests/test_storage.py`
- **Create a configured SQLite connection.** (1 connections) — `src/storage/db.py`
- **Context manager for SQLite database transactions.** (1 connections) — `src/storage/db.py`
- **Update processing status of an article.** (1 connections) — `src/storage/repository.py`
- **Delete a draft creation.** (1 connections) — `src/storage/repository.py`
- **Store or update dense vector embedding for an article.** (1 connections) — `src/storage/repository.py`
- **Retrieve embedding vector for a single article.** (1 connections) — `src/storage/repository.py`

## Relationships

- [StorageRepository](StorageRepository.md) (11 shared connections)
- [llm_client.py](llm_client.py.md) (6 shared connections)
- [ArticleRecord](ArticleRecord.md) (6 shared connections)
- [test_pipeline_job_lifecycle](test_pipeline_job_lifecycle.md) (6 shared connections)
- [.get_article](get_article.md) (4 shared connections)
- [test_drafts_and_creations_workflow](test_drafts_and_creations_workflow.md) (4 shared connections)
- [AppConfig](AppConfig.md) (2 shared connections)
- [LLMClient](LLMClient.md) (2 shared connections)
- [.select_complementary_seeds](select_complementary_seeds.md) (1 shared connections)
- [get_observability_metrics](get_observability_metrics.md) (1 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (1 shared connections)

## Source Files

- `src/storage/db.py`
- `src/storage/repository.py`
- `tests/test_storage.py`

## Audit Trail

- EXTRACTED: 60 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*