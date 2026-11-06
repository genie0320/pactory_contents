# load_config()

> God node · 49 connections · `src/config.py`

**Community:** [LLMClient](LLMClient.md)

## Connections by Relation

### calls
- [AppConfig](AppConfig.md) `EXTRACTED`
- cmd_generate() `EXTRACTED`
- synthesize_draft() `EXTRACTED`
- cmd_extract() `EXTRACTED`
- generate_blueprint() `EXTRACTED`
- scan_inbox() `EXTRACTED`
- get_services() `EXTRACTED`
- get_services() `EXTRACTED`
- search_seed_candidates() `EXTRACTED`
- process_inbox() `EXTRACTED`
- run_style_learning() `EXTRACTED`
- cmd_ingest() `EXTRACTED`
- cmd_learn_style() `EXTRACTED`
- cmd_search() `EXTRACTED`
- save_creation() `EXTRACTED`
- update_creation() `EXTRACTED`
- update_style_profile() `EXTRACTED`
- list_creations() `EXTRACTED`
- get_inbox_stats() `EXTRACTED`
- list_articles() `EXTRACTED`
- *…and 12 more `calls` connection(s) not listed (lowest-degree first to go)*

### contains
- config.py `EXTRACTED`

### imports
- legacy_streamlit_app.py `EXTRACTED`
- [routers/generator.py](routers-generator.py.md) `EXTRACTED`
- app.py `EXTRACTED`
- run.py `EXTRACTED`
- synthesizer.py `EXTRACTED`
- routers/editor.py `EXTRACTED`
- [routers/inbox.py](routers-inbox.py.md) `EXTRACTED`
- routers/style.py `EXTRACTED`
- scanner.py `EXTRACTED`
- retriever.py `EXTRACTED`
- batch_extractor.py `EXTRACTED`
- style_learner.py `EXTRACTED`
- proofreader.py `EXTRACTED`
- observability.py `EXTRACTED`

### rationale_for
- Load configuration from YAML file and environment variables. `EXTRACTED`

### references
- Path `EXTRACTED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*