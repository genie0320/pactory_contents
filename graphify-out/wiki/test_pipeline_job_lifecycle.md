# test_pipeline_job_lifecycle

> 15 nodes · cohesion 0.14

## Key Concepts

- **test_pipeline_job_lifecycle()** (8 connections) — `tests/test_jobs_and_creations.py`
- **.list_creations()** (7 connections) — `src/storage/repository.py`
- **Any** (6 connections)
- **.get_job()** (6 connections) — `src/storage/repository.py`
- **.list_jobs()** (6 connections) — `src/storage/repository.py`
- **.complete_job()** (4 connections) — `src/storage/repository.py`
- **.create_job()** (4 connections) — `src/storage/repository.py`
- **.update_job_progress()** (4 connections) — `src/storage/repository.py`
- **Create a new pipeline job record in RUNNING status.** (1 connections) — `src/storage/repository.py`
- **Increment progress and update status of a pipeline job.** (1 connections) — `src/storage/repository.py`
- **Mark a job as COMPLETED or FAILED.** (1 connections) — `src/storage/repository.py`
- **Fetch job record by job_id as a dictionary.** (1 connections) — `src/storage/repository.py`
- **List recent pipeline jobs.** (1 connections) — `src/storage/repository.py`
- **List creations, optionally filtered by status.** (1 connections) — `src/storage/repository.py`
- **Verify pipeline_jobs creation, incremental progress updates, and completion.** (1 connections) — `tests/test_jobs_and_creations.py`

## Relationships

- [StorageRepository](StorageRepository.md) (7 shared connections)
- [get_db](get_db.md) (6 shared connections)
- [ArticleRecord](ArticleRecord.md) (4 shared connections)
- [LLMClient](LLMClient.md) (2 shared connections)
- [test_drafts_and_creations_workflow](test_drafts_and_creations_workflow.md) (1 shared connections)
- [get_observability_metrics](get_observability_metrics.md) (1 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (1 shared connections)

## Source Files

- `src/storage/repository.py`
- `tests/test_jobs_and_creations.py`

## Audit Trail

- EXTRACTED: 26 (70%)
- INFERRED: 11 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*