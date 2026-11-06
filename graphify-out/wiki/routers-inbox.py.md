# routers/inbox.py

> 70 nodes · cohesion 0.06

## Key Concepts

- **routers/inbox.py** (26 connections) — `src/api/routers/inbox.py`
- **test_ingestion.py** (26 connections) — `tests/test_ingestion.py`
- **IngestionScanner** (25 connections) — `src/ingestion/scanner.py`
- **pdf_processor.py** (17 connections) — `src/ingestion/pdf_processor.py`
- **VisualAssetItem** (14 connections) — `src/models.py`
- **test_10_sample_articles_ingestion()** (14 connections) — `tests/test_ingestion.py`
- **scan_inbox()** (12 connections) — `src/api/routers/inbox.py`
- **schemas/inbox.py** (11 connections) — `src/api/schemas/inbox.py`
- **PDFProcessor** (11 connections) — `src/ingestion/pdf_processor.py`
- **process_inbox()** (10 connections) — `src/api/routers/inbox.py`
- **re** (9 connections)
- **.process_file()** (9 connections) — `src/ingestion/scanner.py`
- **text_normalizer.py** (9 connections) — `src/ingestion/text_normalizer.py`
- **get_inbox_stats()** (8 connections) — `src/api/routers/inbox.py`
- **list_articles()** (8 connections) — `src/api/routers/inbox.py`
- **.process_pdf()** (8 connections) — `src/ingestion/pdf_processor.py`
- **.scan_inbox()** (8 connections) — `src/ingestion/scanner.py`
- **clean_boilerplate()** (8 connections) — `src/ingestion/text_normalizer.py`
- **extract_author_and_date()** (8 connections) — `src/ingestion/text_normalizer.py`
- **.list_articles()** (8 connections) — `src/storage/repository.py`
- **BaseModel** (7 connections)
- **ImageFilterSettings** (7 connections) — `src/config.py`
- **normalize_markdown()** (7 connections) — `src/ingestion/text_normalizer.py`
- **._extract_page_images()** (5 connections) — `src/ingestion/pdf_processor.py`
- **.compute_sha256()** (5 connections) — `src/ingestion/scanner.py`
- *... and 45 more nodes in this community*

## Relationships

- [llm_client.py](llm_client.py.md) (32 shared connections)
- [ArticleRecord](ArticleRecord.md) (14 shared connections)
- [StorageRepository](StorageRepository.md) (12 shared connections)
- [AppConfig](AppConfig.md) (12 shared connections)
- [LLMClient](LLMClient.md) (9 shared connections)
- [routers/generator.py](routers-generator.py.md) (5 shared connections)
- [.get_article](get_article.md) (3 shared connections)
- [StyleLearner](StyleLearner.md) (2 shared connections)
- [test_pipeline_job_lifecycle](test_pipeline_job_lifecycle.md) (1 shared connections)
- [get_db](get_db.md) (1 shared connections)
- [ArticleArchetype](ArticleArchetype.md) (1 shared connections)

## Source Files

- `src/api/routers/inbox.py`
- `src/api/schemas/inbox.py`
- `src/config.py`
- `src/ingestion/pdf_processor.py`
- `src/ingestion/scanner.py`
- `src/ingestion/text_normalizer.py`
- `src/models.py`
- `src/storage/repository.py`
- `tests/test_ingestion.py`
- `tests/test_storage.py`

## Audit Trail

- EXTRACTED: 193 (83%)
- INFERRED: 39 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*