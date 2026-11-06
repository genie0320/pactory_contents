# LLMClient

> 74 nodes · cohesion 0.05

## Key Concepts

- **LLMClient** (64 connections) — `src/extraction/llm_client.py`
- **load_config()** (49 connections) — `src/config.py`
- **routers/editor.py** (31 connections) — `src/api/routers/editor.py`
- **ArticleProofreader** (23 connections) — `src/synthesis/proofreader.py`
- **proofreader.py** (16 connections) — `src/synthesis/proofreader.py`
- **test_proofreader.py** (15 connections) — `tests/test_proofreader.py`
- **schemas/editor.py** (10 connections) — `src/api/schemas/editor.py`
- **exceptions.py** (10 connections) — `src/exceptions.py`
- **proofread_draft()** (9 connections) — `src/api/routers/editor.py`
- **save_creation()** (9 connections) — `src/api/routers/editor.py`
- **update_creation()** (9 connections) — `src/api/routers/editor.py`
- **.review_sync()** (9 connections) — `src/synthesis/proofreader.py`
- **list_creations()** (8 connections) — `src/api/routers/editor.py`
- **.get_creation()** (8 connections) — `src/storage/repository.py`
- **.review()** (8 connections) — `src/synthesis/proofreader.py`
- **get_creation()** (7 connections) — `src/api/routers/editor.py`
- **delete_creation()** (6 connections) — `src/api/routers/editor.py`
- **CreationDetailResponse** (6 connections) — `src/api/schemas/editor.py`
- **BaseModel** (6 connections)
- **._log_observability()** (6 connections) — `src/extraction/llm_client.py`
- **._parse_llm_response()** (6 connections) — `src/synthesis/proofreader.py`
- **test_proofreader_raises_when_no_api_key()** (6 connections) — `tests/test_proofreader.py`
- **.__init__()** (5 connections) — `src/extraction/batch_extractor.py`
- **.__init__()** (5 connections) — `src/storage/retriever.py`
- **.split_frontmatter()** (5 connections) — `src/synthesis/proofreader.py`
- *... and 49 more nodes in this community*

## Relationships

- [llm_client.py](llm_client.py.md) (38 shared connections)
- [AppConfig](AppConfig.md) (20 shared connections)
- [routers/generator.py](routers-generator.py.md) (17 shared connections)
- [StyleLearner](StyleLearner.md) (14 shared connections)
- [LLMServiceError](LLMServiceError.md) (12 shared connections)
- [ArticleArchetype](ArticleArchetype.md) (11 shared connections)
- [StorageRepository](StorageRepository.md) (10 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (9 shared connections)
- [ArticleRecord](ArticleRecord.md) (5 shared connections)
- [MaterialDistiller](MaterialDistiller.md) (4 shared connections)
- [test_drafts_and_creations_workflow](test_drafts_and_creations_workflow.md) (3 shared connections)
- [get_db](get_db.md) (2 shared connections)

## Source Files

- `src/api/routers/editor.py`
- `src/api/schemas/editor.py`
- `src/config.py`
- `src/exceptions.py`
- `src/extraction/batch_extractor.py`
- `src/extraction/llm_client.py`
- `src/storage/repository.py`
- `src/storage/retriever.py`
- `src/synthesis/planner.py`
- `src/synthesis/proofreader.py`
- `src/synthesis/style_learner.py`
- `tests/test_proofreader.py`

## Audit Trail

- EXTRACTED: 239 (81%)
- INFERRED: 56 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*