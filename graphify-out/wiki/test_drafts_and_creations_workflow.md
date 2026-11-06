# test_drafts_and_creations_workflow

> 10 nodes · cohesion 0.20

## Key Concepts

- **test_drafts_and_creations_workflow()** (8 connections) — `tests/test_jobs_and_creations.py`
- **.save_draft_creation()** (6 connections) — `src/storage/repository.py`
- **.get_finalized_creations_for_learning()** (5 connections) — `src/storage/repository.py`
- **.update_creation_final()** (5 connections) — `src/storage/repository.py`
- **.mark_creations_used_for_style()** (4 connections) — `src/storage/repository.py`
- **Save a generated draft into drafts_and_creations table.** (1 connections) — `src/storage/repository.py`
- **Update draft to FINALIZED with user modifications.** (1 connections) — `src/storage/repository.py`
- **Fetch finalized creations with user_final_text that have not been learned yet.…** (1 connections) — `src/storage/repository.py`
- **Mark creation records as used_for_style_learning = 1.** (1 connections) — `src/storage/repository.py`
- **Verify saving draft, listing drafts, updating to finalized, and query for…** (1 connections) — `tests/test_jobs_and_creations.py`

## Relationships

- [StorageRepository](StorageRepository.md) (5 shared connections)
- [get_db](get_db.md) (4 shared connections)
- [LLMClient](LLMClient.md) (3 shared connections)
- [test_pipeline_job_lifecycle](test_pipeline_job_lifecycle.md) (1 shared connections)
- [routers/generator.py](routers-generator.py.md) (1 shared connections)
- [ArticleRecord](ArticleRecord.md) (1 shared connections)

## Source Files

- `src/storage/repository.py`
- `tests/test_jobs_and_creations.py`

## Audit Trail

- EXTRACTED: 15 (62%)
- INFERRED: 9 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*