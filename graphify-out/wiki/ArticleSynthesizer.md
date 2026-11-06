# ArticleSynthesizer

> God node · 32 connections · `src/synthesis/synthesizer.py`

**Community:** [AppConfig](AppConfig.md)

## Connections by Relation

### calls
- test_synthesizer_job_and_creation_recording() `EXTRACTED`
- get_services() `EXTRACTED`
- get_services() `EXTRACTED`

### contains
- synthesizer.py `EXTRACTED`

### imports
- legacy_streamlit_app.py `EXTRACTED`
- [routers/generator.py](routers-generator.py.md) `EXTRACTED`
- app.py `EXTRACTED`
- run.py `EXTRACTED`
- test_distiller.py `EXTRACTED`
- test_style_learner.py `EXTRACTED`
- test_synthesizer.py `EXTRACTED`
- test_jobs_and_creations.py `EXTRACTED`

### method
- .synthesize_sync() `EXTRACTED`
- .synthesize() `EXTRACTED`
- .__init__() `EXTRACTED`
- .slugify() `EXTRACTED`

### rationale_for
- Orchestrates Blueprint planning, material distillation, and neutral draft… `EXTRACTED`

### uses
- [StorageRepository](StorageRepository.md) `INFERRED`
- [LLMClient](LLMClient.md) `INFERRED`
- [ArticleArchetype](ArticleArchetype.md) `INFERRED`
- [AppConfig](AppConfig.md) `INFERRED`
- [SeedRoleAssignment](SeedRoleAssignment.md) `INFERRED`
- SynthesisBlueprint `INFERRED`
- SynthesisPlanner `INFERRED`
- cmd_generate() `INFERRED`
- UserStyleProfile `INFERRED`
- [DistilledMaterialSheet](DistilledMaterialSheet.md) `INFERRED`
- synthesize_draft() `INFERRED`
- [MaterialDistiller](MaterialDistiller.md) `INFERRED`
- distillation_env() `INFERRED`
- synthesizer_env() `INFERRED`
- style_env() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*