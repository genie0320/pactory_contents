# .get_article

> 8 nodes · cohesion 0.25

## Key Concepts

- **.get_article()** (10 connections) — `src/storage/repository.py`
- **.save_article_metadata()** (8 connections) — `src/storage/repository.py`
- **.get_visual_assets()** (5 connections) — `src/storage/repository.py`
- **.delete_article()** (4 connections) — `src/storage/repository.py`
- **Delete an article and its related metadata, assets, and FTS index.** (1 connections) — `src/storage/repository.py`
- **Fetch visual assets for doc_id.** (1 connections) — `src/storage/repository.py`
- **Save metadata atomically: 1. Write data/processed/metadata/{doc_id}.json 2.…** (1 connections) — `src/storage/repository.py`
- **Fetch article by doc_id.** (1 connections) — `src/storage/repository.py`

## Relationships

- [StorageRepository](StorageRepository.md) (5 shared connections)
- [get_db](get_db.md) (4 shared connections)
- [ArticleRecord](ArticleRecord.md) (3 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (3 shared connections)
- [routers/generator.py](routers-generator.py.md) (1 shared connections)
- [AppConfig](AppConfig.md) (1 shared connections)

## Source Files

- `src/storage/repository.py`

## Audit Trail

- EXTRACTED: 20 (83%)
- INFERRED: 4 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*