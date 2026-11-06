# .select_complementary_seeds

> 15 nodes · cohesion 0.15

## Key Concepts

- **.select_complementary_seeds()** (11 connections) — `src/storage/retriever.py`
- **.search_candidates()** (9 connections) — `src/storage/retriever.py`
- **.extract_keywords()** (5 connections) — `src/storage/retriever.py`
- **.cosine_similarity()** (4 connections) — `src/storage/retriever.py`
- **.jaccard_similarity()** (4 connections) — `src/storage/retriever.py`
- **test_jaccard_and_keyword_extraction()** (4 connections) — `tests/test_retriever.py`
- **test_cosine_similarity()** (3 connections) — `tests/test_retriever.py`
- **score_seed2()** (2 connections) — `src/storage/retriever.py`
- **Compute Jaccard similarity between two tag lists.** (1 connections) — `src/storage/retriever.py`
- **Hybrid retrieval combining FTS5 BM25 (keyword matching) and Dense Vector…** (1 connections) — `src/storage/retriever.py`
- **Stage 2: Role-based complementary seed selection. - Seed #1 (Domain & Case…** (1 connections) — `src/storage/retriever.py`
- **Compute cosine similarity between two dense vectors.** (1 connections) — `src/storage/retriever.py`
- **Extract meaningful keywords stripping Korean particles, predicate endings, and…** (1 connections) — `src/storage/retriever.py`
- **score_seed1()** (1 connections) — `src/storage/retriever.py`
- **score_seed3()** (1 connections) — `src/storage/retriever.py`

## Relationships

- [AppConfig](AppConfig.md) (9 shared connections)
- [ArticleRecord](ArticleRecord.md) (2 shared connections)
- [ArticleArchetype](ArticleArchetype.md) (2 shared connections)
- [StyleLearner](StyleLearner.md) (2 shared connections)
- [get_db](get_db.md) (1 shared connections)
- [routers/generator.py](routers-generator.py.md) (1 shared connections)

## Source Files

- `src/storage/retriever.py`
- `tests/test_retriever.py`

## Audit Trail

- EXTRACTED: 25 (76%)
- INFERRED: 8 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*