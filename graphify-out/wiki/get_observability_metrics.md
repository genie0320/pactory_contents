# get_observability_metrics

> 6 nodes · cohesion 0.33

## Key Concepts

- **get_observability_metrics()** (7 connections) — `src/api/routers/observability.py`
- **.get_observability_stats()** (5 connections) — `src/storage/repository.py`
- **Any** (1 connections)
- **get** (1 connections)
- **Retrieve cumulative LLM token consumption, latency, and estimated cost.** (1 connections) — `src/api/routers/observability.py`
- **Aggregate total tokens, invocations, average latency, and estimated cost.** (1 connections) — `src/storage/repository.py`

## Relationships

- [StorageRepository](StorageRepository.md) (2 shared connections)
- [LLMClient](LLMClient.md) (1 shared connections)
- [routers/generator.py](routers-generator.py.md) (1 shared connections)
- [get_db](get_db.md) (1 shared connections)
- [test_pipeline_job_lifecycle](test_pipeline_job_lifecycle.md) (1 shared connections)

## Source Files

- `src/api/routers/observability.py`
- `src/storage/repository.py`

## Audit Trail

- EXTRACTED: 9 (82%)
- INFERRED: 2 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*