# AppConfig

> 34 nodes · cohesion 0.11

## Key Concepts

- **AppConfig** (34 connections) — `src/config.py`
- **init_db()** (33 connections) — `src/storage/db.py`
- **ArticleSynthesizer** (32 connections) — `src/synthesis/synthesizer.py`
- **SeedRetriever** (31 connections) — `src/storage/retriever.py`
- **test_style_learner.py** (27 connections) — `tests/test_style_learner.py`
- **test_retriever.py** (23 connections) — `tests/test_retriever.py`
- **populated_retriever()** (16 connections) — `tests/test_retriever.py`
- **PathSettings** (14 connections) — `src/config.py`
- **synthesizer_env()** (12 connections) — `tests/test_synthesizer.py`
- **get_services()** (11 connections) — `archive/legacy_streamlit_app.py`
- **get_services()** (11 connections) — `src/ui/app.py`
- **extraction_env()** (11 connections) — `tests/test_extraction.py`
- **style_env()** (11 connections) — `tests/test_style_learner.py`
- **.ensure_directories()** (8 connections) — `src/config.py`
- **BaseModel** (6 connections)
- **ExtractionSettings** (4 connections) — `src/config.py`
- **RetrievalSettings** (2 connections) — `src/config.py`
- **TaxonomySettings** (2 connections) — `src/config.py`
- **test_complementary_seed_selection()** (2 connections) — `tests/test_retriever.py`
- **Create runtime data directories if they do not exist.** (1 connections) — `src/config.py`
- **Initialize database tables and FTS5 virtual tables.** (1 connections) — `src/storage/db.py`
- **Retrieves and ranks complementary Seed articles based on Hybrid FTS5 BM25 +…** (1 connections) — `src/storage/retriever.py`
- **Orchestrates Blueprint planning, material distillation, and neutral draft…** (1 connections) — `src/synthesis/synthesizer.py`
- **fixture** (1 connections)
- **Path** (1 connections)
- *... and 9 more nodes in this community*

## Relationships

- [llm_client.py](llm_client.py.md) (42 shared connections)
- [ArticleArchetype](ArticleArchetype.md) (28 shared connections)
- [ArticleRecord](ArticleRecord.md) (25 shared connections)
- [LLMClient](LLMClient.md) (20 shared connections)
- [StorageRepository](StorageRepository.md) (13 shared connections)
- [StyleLearner](StyleLearner.md) (13 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (12 shared connections)
- [DistilledMaterialSheet](DistilledMaterialSheet.md) (9 shared connections)
- [.select_complementary_seeds](select_complementary_seeds.md) (9 shared connections)
- [routers/generator.py](routers-generator.py.md) (6 shared connections)
- [MaterialDistiller](MaterialDistiller.md) (3 shared connections)
- [get_db](get_db.md) (2 shared connections)

## Source Files

- `archive/legacy_streamlit_app.py`
- `src/config.py`
- `src/storage/db.py`
- `src/storage/retriever.py`
- `src/synthesis/synthesizer.py`
- `src/ui/app.py`
- `tests/test_extraction.py`
- `tests/test_retriever.py`
- `tests/test_style_learner.py`
- `tests/test_synthesizer.py`

## Audit Trail

- EXTRACTED: 174 (71%)
- INFERRED: 71 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*