# ArticleArchetype

> 41 nodes · cohesion 0.11

## Key Concepts

- **ArticleArchetype** (41 connections) — `src/models.py`
- **SeedRoleAssignment** (33 connections) — `src/models.py`
- **test_distiller.py** (29 connections) — `tests/test_distiller.py`
- **SynthesisBlueprint** (27 connections) — `src/models.py`
- **test_synthesizer.py** (25 connections) — `tests/test_synthesizer.py`
- **SynthesisPlanner** (22 connections) — `src/synthesis/planner.py`
- **ReusableAssetType** (19 connections) — `src/models.py`
- **planner.py** (16 connections) — `src/synthesis/planner.py`
- **test_planner.py** (15 connections) — `tests/test_planner.py`
- **pytest** (12 connections)
- **test_blueprint_planner()** (9 connections) — `tests/test_synthesizer.py`
- **.plan_blueprint_sync()** (8 connections) — `src/synthesis/planner.py`
- **test_planner_sync_execution()** (7 connections) — `tests/test_planner.py`
- **test_style_learning_cycle()** (7 connections) — `tests/test_style_learner.py`
- **.plan_blueprint()** (6 connections) — `src/synthesis/planner.py`
- **test_material_distillation()** (6 connections) — `tests/test_distiller.py`
- **test_planner_archetype_fallback()** (6 connections) — `tests/test_planner.py`
- **test_draft_synthesis_output_creation()** (6 connections) — `tests/test_synthesizer.py`
- **test_synthesis_without_raw_text_anchoring()** (5 connections) — `tests/test_distiller.py`
- **sample_seeds()** (5 connections) — `tests/test_planner.py`
- **Enum** (4 connections)
- **str** (3 connections)
- **초안 작성 전 선별된 Seed들을 어떻게 엮을지 정의하는 합성 설계도** (1 connections) — `src/models.py`
- **.core_thesis()** (1 connections) — `src/models.py`
- **.hook_strategy()** (1 connections) — `src/models.py`
- *... and 16 more nodes in this community*

## Relationships

- [llm_client.py](llm_client.py.md) (40 shared connections)
- [ArticleRecord](ArticleRecord.md) (28 shared connections)
- [AppConfig](AppConfig.md) (28 shared connections)
- [DistilledMaterialSheet](DistilledMaterialSheet.md) (12 shared connections)
- [LLMClient](LLMClient.md) (11 shared connections)
- [routers/generator.py](routers-generator.py.md) (11 shared connections)
- [MaterialDistiller](MaterialDistiller.md) (7 shared connections)
- [test_api.py](test_api.py.md) (3 shared connections)
- [.select_complementary_seeds](select_complementary_seeds.md) (2 shared connections)
- [StyleLearner](StyleLearner.md) (2 shared connections)
- [StorageRepository](StorageRepository.md) (2 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (1 shared connections)

## Source Files

- `src/models.py`
- `src/synthesis/planner.py`
- `tests/test_distiller.py`
- `tests/test_planner.py`
- `tests/test_style_learner.py`
- `tests/test_synthesizer.py`

## Audit Trail

- EXTRACTED: 189 (79%)
- INFERRED: 50 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*