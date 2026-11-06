# StorageRepository

> 19 nodes · cohesion 0.12

## Key Concepts

- **StorageRepository** (107 connections) — `src/storage/repository.py`
- **.save_processed_text()** (8 connections) — `src/storage/repository.py`
- **.save_visual_assets()** (6 connections) — `src/storage/repository.py`
- **.get_article_by_title()** (5 connections) — `src/storage/repository.py`
- **.get_article_metadata()** (5 connections) — `src/storage/repository.py`
- **Path** (4 connections)
- **.delete_job()** (3 connections) — `src/storage/repository.py`
- **._ensure_dirs()** (3 connections) — `src/storage/repository.py`
- **.get_all_embeddings()** (3 connections) — `src/storage/repository.py`
- **.__init__()** (3 connections) — `src/storage/repository.py`
- **.log_llm_usage()** (3 connections) — `src/storage/repository.py`
- **Fetch article by exact title.** (1 connections) — `src/storage/repository.py`
- **Manages SQLite database records and filesystem assets.** (1 connections) — `src/storage/repository.py`
- **Save cleaned markdown text to data/processed/texts/{doc_id}.md.** (1 connections) — `src/storage/repository.py`
- **Save visual assets to article_assets table and manifest.json.** (1 connections) — `src/storage/repository.py`
- **Retrieve ArticleMetadata from SQLite or JSON file fallback.** (1 connections) — `src/storage/repository.py`
- **Delete a single job log.** (1 connections) — `src/storage/repository.py`
- **Retrieve all stored embedding vectors as a map of doc_id -> vector.** (1 connections) — `src/storage/repository.py`
- **Log token count, latency, and cost for an LLM invocation.** (1 connections) — `src/storage/repository.py`

## Relationships

- [ArticleRecord](ArticleRecord.md) (17 shared connections)
- [AppConfig](AppConfig.md) (13 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (12 shared connections)
- [llm_client.py](llm_client.py.md) (12 shared connections)
- [get_db](get_db.md) (11 shared connections)
- [LLMClient](LLMClient.md) (10 shared connections)
- [routers/generator.py](routers-generator.py.md) (7 shared connections)
- [test_pipeline_job_lifecycle](test_pipeline_job_lifecycle.md) (7 shared connections)
- [.get_article](get_article.md) (5 shared connections)
- [StyleLearner](StyleLearner.md) (5 shared connections)
- [test_drafts_and_creations_workflow](test_drafts_and_creations_workflow.md) (5 shared connections)
- [MaterialDistiller](MaterialDistiller.md) (4 shared connections)

## Source Files

- `src/storage/repository.py`

## Audit Trail

- EXTRACTED: 92 (67%)
- INFERRED: 45 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*