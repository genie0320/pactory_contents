# LLMClient

> God node · 64 connections · `src/extraction/llm_client.py`

**Community:** [LLMClient](LLMClient.md)

## Connections by Relation

### calls
- get_services() `EXTRACTED`
- get_services() `EXTRACTED`
- test_blueprint_planner() `EXTRACTED`

### contains
- [llm_client.py](llm_client.py.md) `EXTRACTED`

### imports
- legacy_streamlit_app.py `EXTRACTED`
- [routers/generator.py](routers-generator.py.md) `EXTRACTED`
- app.py `EXTRACTED`
- run.py `EXTRACTED`
- synthesizer.py `EXTRACTED`
- routers/editor.py `EXTRACTED`
- test_distiller.py `EXTRACTED`
- test_style_learner.py `EXTRACTED`
- [routers/inbox.py](routers-inbox.py.md) `EXTRACTED`
- routers/style.py `EXTRACTED`
- retriever.py `EXTRACTED`
- test_synthesizer.py `EXTRACTED`
- test_extraction.py `EXTRACTED`
- batch_extractor.py `EXTRACTED`
- style_learner.py `EXTRACTED`
- planner.py `EXTRACTED`
- proofreader.py `EXTRACTED`
- test_planner.py `EXTRACTED`
- test_proofreader.py `EXTRACTED`
- distiller.py `EXTRACTED`

### method
- .__init__() `EXTRACTED`
- ._log_observability() `EXTRACTED`
- .extract_structured() `EXTRACTED`
- .extract_structured_sync() `EXTRACTED`
- .generate_text() `EXTRACTED`
- .generate_text_sync() `EXTRACTED`
- .get_embedding() `EXTRACTED`
- .get_embedding_sync() `EXTRACTED`

### rationale_for
- Universal LLM client orchestrating providers and tracking usage/latency. `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`

### uses
- [ArticleSynthesizer](ArticleSynthesizer.md) `INFERRED`
- SeedRetriever `INFERRED`
- [StyleLearner](StyleLearner.md) `INFERRED`
- BatchMetadataExtractor `INFERRED`
- ArticleProofreader `INFERRED`
- SynthesisPlanner `INFERRED`
- cmd_generate() `INFERRED`
- synthesize_draft() `INFERRED`
- [MaterialDistiller](MaterialDistiller.md) `INFERRED`
- distillation_env() `INFERRED`
- cmd_extract() `INFERRED`
- generate_blueprint() `INFERRED`
- synthesizer_env() `INFERRED`
- extraction_env() `INFERRED`
- style_env() `INFERRED`
- process_inbox() `INFERRED`
- run_style_learning() `INFERRED`
- proofread_draft() `INFERRED`
- test_planner_sync_execution() `INFERRED`
- test_planner_archetype_fallback() `INFERRED`
- *…and 4 more `uses` connection(s) not listed (lowest-degree first to go)*

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*