# DistilledMaterialSheet

> 13 nodes · cohesion 0.19

## Key Concepts

- **DistilledMaterialSheet** (17 connections) — `src/models.py`
- **distillation_env()** (16 connections) — `tests/test_distiller.py`
- **.synthesize()** (11 connections) — `src/synthesis/synthesizer.py`
- **.synthesize_sync()** (11 connections) — `src/synthesis/synthesizer.py`
- **.slugify()** (4 connections) — `src/synthesis/synthesizer.py`
- **mock_extract()** (3 connections) — `tests/test_distiller.py`
- **Path** (2 connections)
- **[v2.0] 초안이 Seed의 문장과 포맷을 모방하지 않도록 원문에서 알맹이만 발췌한 건조한 개조식 재료 시트** (1 connections) — `src/models.py`
- **Synchronous version for offline/sandbox mode.** (1 connections) — `src/synthesis/synthesizer.py`
- **Create filesystem-safe ASCII slug.** (1 connections) — `src/synthesis/synthesizer.py`
- **v2.0 3-Stage Synthesis Pipeline: 1. Plan blueprint from metadata 2. Distill…** (1 connections) — `src/synthesis/synthesizer.py`
- **fixture** (1 connections)
- **Path** (1 connections)

## Relationships

- [ArticleArchetype](ArticleArchetype.md) (12 shared connections)
- [AppConfig](AppConfig.md) (9 shared connections)
- [MaterialDistiller](MaterialDistiller.md) (6 shared connections)
- [llm_client.py](llm_client.py.md) (5 shared connections)
- [ArticleRecord](ArticleRecord.md) (2 shared connections)
- [StyleLearner](StyleLearner.md) (2 shared connections)
- [StorageRepository](StorageRepository.md) (2 shared connections)
- [routers/generator.py](routers-generator.py.md) (1 shared connections)
- [LLMClient](LLMClient.md) (1 shared connections)

## Source Files

- `src/models.py`
- `src/synthesis/synthesizer.py`
- `tests/test_distiller.py`

## Audit Trail

- EXTRACTED: 36 (65%)
- INFERRED: 19 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*