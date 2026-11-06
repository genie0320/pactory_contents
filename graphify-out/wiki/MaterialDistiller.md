# MaterialDistiller

> 13 nodes · cohesion 0.21

## Key Concepts

- **MaterialDistiller** (16 connections) — `src/synthesis/distiller.py`
- **.__init__()** (7 connections) — `src/synthesis/synthesizer.py`
- **.distill_seed()** (6 connections) — `src/synthesis/distiller.py`
- **.distill_seed_sync()** (6 connections) — `src/synthesis/distiller.py`
- **.distill_all()** (5 connections) — `src/synthesis/distiller.py`
- **.distill_all_sync()** (5 connections) — `src/synthesis/distiller.py`
- **.get_processed_text()** (4 connections) — `src/storage/repository.py`
- **.__init__()** (3 connections) — `src/synthesis/distiller.py`
- **Distill all selected seeds asynchronously.** (2 connections) — `src/synthesis/distiller.py`
- **Read cleaned text for doc_id.** (1 connections) — `src/storage/repository.py`
- **Distills raw text into de-contextualized, bulleted fact & mechanism sheets.** (1 connections) — `src/synthesis/distiller.py`
- **Distill a single seed article into DistilledMaterialSheet.** (1 connections) — `src/synthesis/distiller.py`
- **Synchronous distillation for offline/sandbox mode.** (1 connections) — `src/synthesis/distiller.py`

## Relationships

- [ArticleArchetype](ArticleArchetype.md) (7 shared connections)
- [DistilledMaterialSheet](DistilledMaterialSheet.md) (6 shared connections)
- [StorageRepository](StorageRepository.md) (4 shared connections)
- [LLMClient](LLMClient.md) (4 shared connections)
- [AppConfig](AppConfig.md) (3 shared connections)
- [llm_client.py](llm_client.py.md) (2 shared connections)

## Source Files

- `src/storage/repository.py`
- `src/synthesis/distiller.py`
- `src/synthesis/synthesizer.py`

## Audit Trail

- EXTRACTED: 34 (81%)
- INFERRED: 8 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*