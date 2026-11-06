# Graph Report - pactory_contents  (2026-11-06)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 924 nodes · 2213 edges · 73 communities (24 shown, 49 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 302 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `34cfb9aa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LLMClient
- routers/inbox.py
- LLMServiceError
- routers/generator.py
- llm_client.py
- StyleLearner
- ArticleArchetype
- ArticleRecord
- paths
- AppConfig
- package.json
- test_api.py
- compilerOptions
- client.ts
- StorageRepository
- pactory-studio
- compilerOptions
- get_db
- App.tsx
- Navbar.tsx
- test_pipeline_job_lifecycle
- .select_complementary_seeds
- DistilledMaterialSheet
- MaterialDistiller
- dependencies
- test_drafts_and_creations_workflow
- .oxlintrc.json
- get_observability_metrics
- scripts
- show_lightbox_dialog
- resolve_asset_path
- 4950/manifest.json
- 4951/manifest.json
- 4952/manifest.json
- 4958/manifest.json
- 4959/manifest.json
- 5454/manifest.json
- 5455/manifest.json
- 5456/manifest.json
- 5457/manifest.json
- 5458/manifest.json
- 5466/manifest.json
- 5530/manifest.json
- 7115/manifest.json
- 7117/manifest.json
- 7118/manifest.json
- 7120/manifest.json
- 7121/manifest.json
- 7123/manifest.json
- 7125/manifest.json
- 7126/manifest.json
- tsconfig.json
- show_lightbox_dialog
- resolve_asset_path
- repo
- temp_storage
- reset_generator_state
- backup_daily.sh
- run_pipeline.sh
- reset_generator_state
- seed-synthesis-engine

## God Nodes (most connected - your core abstractions)
1. `StorageRepository` - 107 edges
2. `LLMClient` - 64 edges
3. `load_config()` - 49 edges
4. `ArticleArchetype` - 41 edges
5. `get_db()` - 36 edges
6. `ArticleRecord` - 35 edges
7. `AppConfig` - 34 edges
8. `SeedRoleAssignment` - 33 edges
9. `init_db()` - 33 edges
10. `ArticleSynthesizer` - 32 edges

## Surprising Connections (you probably didn't know these)
- `test_complementary_seed_selection()` --uses--> `ArticleArchetype`  [INFERRED]
  tests/test_retriever.py → src/models.py
- `cmd_extract()` --uses--> `LLMClient`  [INFERRED]
  run.py → src/extraction/llm_client.py
- `cmd_generate()` --uses--> `LLMClient`  [INFERRED]
  run.py → src/extraction/llm_client.py
- `distillation_env()` --uses--> `LLMClient`  [INFERRED]
  tests/test_distiller.py → src/extraction/llm_client.py
- `extraction_env()` --uses--> `LLMClient`  [INFERRED]
  tests/test_extraction.py → src/extraction/llm_client.py

## Import Cycles
- None detected.

## Communities (73 total, 49 thin omitted)

### Community 0 - "LLMClient"
Cohesion: 0.05
Nodes (21): delete_creation(), _extract_title_from_text(), get_creation(), list_creations(), proofread_draft(), save_creation(), update_creation(), CreationDetailResponse (+13 more)

### Community 1 - "routers/inbox.py"
Cohesion: 0.06
Nodes (23): get_inbox_stats(), list_articles(), process_inbox(), scan_inbox(), ArticleListResponse, ArticleSummaryItem, InboxFileItem, InboxProcessRequest (+15 more)

### Community 2 - "LLMServiceError"
Cohesion: 0.05
Nodes (13): LLMServiceError, BaseLLMProvider, ClaudeProvider, _clean_and_parse_json(), GeminiProvider, _call(), _call(), is_retryable_error() (+5 more)

### Community 3 - "routers/generator.py"
Cohesion: 0.06
Nodes (24): get_configured_password(), LoginRequest, LoginResponse, verify_auth(), auth_status(), health_check(), llm_service_error_handler(), login() (+16 more)

### Community 4 - "llm_client.py"
Cohesion: 0.10
Nodes (3): load_env_file(), UserStyleProfile, VisualAssetManifest

### Community 5 - "StyleLearner"
Cohesion: 0.06
Nodes (15): cmd_generate(), cmd_ingest(), cmd_init(), cmd_learn_style(), cmd_pipeline(), cmd_search(), cmd_ui(), get_style_profile() (+7 more)

### Community 6 - "ArticleArchetype"
Cohesion: 0.11
Nodes (13): ArticleArchetype, ReusableAssetType, SeedRoleAssignment, SynthesisBlueprint, SynthesisPlanner, test_material_distillation(), test_synthesis_without_raw_text_anchoring(), sample_seeds() (+5 more)

### Community 7 - "ArticleRecord"
Cohesion: 0.10
Nodes (11): cmd_extract(), BatchMetadataExtractor, ArticleMetadata, ArticleRecord, ArticleStatus, test_fault_tolerant_checkpointing_resumption(), test_structured_metadata_extraction(), test_batch_extractor_job_tracking() (+3 more)

### Community 8 - "paths"
Cohesion: 0.06
Nodes (34): core_problem, notable_episodes, reframing_logic, solution_framework, title, topic_tags, extraction, concurrency (+26 more)

### Community 9 - "AppConfig"
Cohesion: 0.11
Nodes (15): get_services(), AppConfig, ExtractionSettings, PathSettings, RetrievalSettings, TaxonomySettings, init_db(), SeedRetriever (+7 more)

### Community 10 - "package.json"
Cohesion: 0.12
Nodes (21): @tailwindcss/vite@^4.3.4, devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6 (+13 more)

### Community 11 - "test_api.py"
Cohesion: 0.10
Nodes (8): test_auth_rejection_and_login(), test_creations_crud_lifecycle(), test_health_check(), test_inbox_endpoints(), test_observability_endpoint(), test_proofread_endpoint_mocked(), test_seed_search_endpoint(), test_style_endpoints()

### Community 12 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 13 - "client.ts"
Cohesion: 0.16
Nodes (15): lucide-react@^1.69.0, api, ArticleSummaryItem, CreationDetailResponse, CreationSummaryItem, DraftSynthesizeResponse, editorApi, inboxApi (+7 more)

### Community 15 - "pactory-studio"
Cohesion: 0.12
Nodes (16): context, dockerfile, interval, retries, start_period, test, timeout, build (+8 more)

### Community 16 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "get_db"
Cohesion: 0.14
Nodes (3): get_connection(), get_db(), test_init_db_creates_tables()

### Community 18 - "App.tsx"
Cohesion: 0.23
Nodes (11): authApi, App(), AuthModal(), AuthModalProps, Navbar(), InboxPage(), LibraryPage(), StudioEditorPage() (+3 more)

### Community 19 - "Navbar.tsx"
Cohesion: 0.17
Nodes (13): BlueprintResponse, draftApi, observabilityApi, ObservabilityStats, SeedCandidateItem, NavbarProps, NavTab, ARCHETYPES (+5 more)

### Community 21 - ".select_complementary_seeds"
Cohesion: 0.15
Nodes (3): score_seed2(), test_cosine_similarity(), test_jaccard_and_keyword_extraction()

### Community 22 - "DistilledMaterialSheet"
Cohesion: 0.19
Nodes (3): DistilledMaterialSheet, distillation_env(), mock_extract()

### Community 24 - "dependencies"
Cohesion: 0.20
Nodes (10): dependencies, axios@^1.21.0, react@^19.3.1, react-dom@^19.3.1, tailwindcss@^4.3.4, zustand@^5.0.16, axios, react-dom (+2 more)

### Community 27 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 29 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, lint, preview

## Knowledge Gaps
- **1 isolated node(s):** `seed-synthesis-engine`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 435 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `StorageRepository` connect `StorageRepository` to `LLMClient`, `routers/inbox.py`, `routers/generator.py`, `llm_client.py`, `StyleLearner`, `ArticleArchetype`, `ArticleRecord`, `AppConfig`, `get_db`, `test_pipeline_job_lifecycle`, `DistilledMaterialSheet`, `MaterialDistiller`, `repo`, `test_drafts_and_creations_workflow`, `.get_article`, `get_observability_metrics`, `temp_storage`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `StorageRepository` (e.g. with `delete_creation()` and `get_creation()`) actually correct?**
  _`StorageRepository` has 39 INFERRED edges - model-reasoned connections that need verification._
- **What connects `seed-synthesis-engine` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `LLMClient` be split into smaller, more focused modules?**
  _Cohesion score 0.05368382080710848 - nodes in this community are weakly interconnected._
- **Why does `LLMClient` connect `LLMClient` to `routers/inbox.py`, `LLMServiceError`, `routers/generator.py`, `llm_client.py`, `StyleLearner`, `ArticleArchetype`, `ArticleRecord`, `AppConfig`, `DistilledMaterialSheet`, `MaterialDistiller`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `LLMClient` (e.g. with `cmd_extract()` and `cmd_generate()`) actually correct?**
  _`LLMClient` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Should `routers/inbox.py` be split into smaller, more focused modules?**
  _Cohesion score 0.057971014492753624 - nodes in this community are weakly interconnected._