# StyleLearner

> 53 nodes · cohesion 0.06

## Key Concepts

- **StyleLearner** (27 connections) — `src/synthesis/style_learner.py`
- **routers/style.py** (26 connections) — `src/api/routers/style.py`
- **cmd_generate()** (18 connections) — `run.py`
- **run_style_learning()** (10 connections) — `src/api/routers/style.py`
- **cmd_ingest()** (9 connections) — `run.py`
- **cmd_learn_style()** (9 connections) — `run.py`
- **cmd_search()** (9 connections) — `run.py`
- **update_style_profile()** (9 connections) — `src/api/routers/style.py`
- **command** (8 connections)
- **Path** (8 connections)
- **get_style_profile()** (8 connections) — `src/api/routers/style.py`
- **schemas/style.py** (8 connections) — `src/api/schemas/style.py`
- **cmd_pipeline()** (7 connections) — `run.py`
- **cmd_init()** (6 connections) — `run.py`
- **.learn_style()** (6 connections) — `src/synthesis/style_learner.py`
- **.learn_style_sync()** (6 connections) — `src/synthesis/style_learner.py`
- **StyleProfileResponse** (5 connections) — `src/api/schemas/style.py`
- **.get_active_profile()** (5 connections) — `src/synthesis/style_learner.py`
- **.get_finalized_candidates()** (5 connections) — `src/synthesis/style_learner.py`
- **._prepare_diff_payload()** (5 connections) — `src/synthesis/style_learner.py`
- **cmd_ui()** (4 connections) — `run.py`
- **BaseModel** (4 connections)
- **StyleLearnRequest** (4 connections) — `src/api/schemas/style.py`
- **StyleLearnResponse** (4 connections) — `src/api/schemas/style.py`
- **StyleUpdateRequest** (4 connections) — `src/api/schemas/style.py`
- *... and 28 more nodes in this community*

## Relationships

- [llm_client.py](llm_client.py.md) (28 shared connections)
- [LLMClient](LLMClient.md) (14 shared connections)
- [AppConfig](AppConfig.md) (13 shared connections)
- [StorageRepository](StorageRepository.md) (5 shared connections)
- [routers/generator.py](routers-generator.py.md) (5 shared connections)
- [ArticleRecord](ArticleRecord.md) (3 shared connections)
- [.select_complementary_seeds](select_complementary_seeds.md) (2 shared connections)
- [DistilledMaterialSheet](DistilledMaterialSheet.md) (2 shared connections)
- [ArticleArchetype](ArticleArchetype.md) (2 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (2 shared connections)

## Source Files

- `run.py`
- `src/api/routers/style.py`
- `src/api/schemas/style.py`
- `src/synthesis/style_learner.py`

## Audit Trail

- EXTRACTED: 125 (77%)
- INFERRED: 37 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*