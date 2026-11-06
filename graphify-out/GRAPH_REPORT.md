# Graph Report - pactory_contents  (2026-11-06)

## Corpus Check
- 116 files · ~139,798 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 5, .service 3, .bat 2)

## Summary
- 935 nodes · 2218 edges · 83 communities (32 shown, 51 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 268 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9ff1c3a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- routers/editor.py
- routers/inbox.py
- BaseLLMProvider
- routers/generator.py
- llm_client.py
- StyleLearner
- ArticleArchetype
- ArticleRecord
- paths
- config.py
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
- scanner.py
- LLMClient
- dependencies
- test_drafts_and_creations_workflow
- ArticleProofreader
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
- BatchMetadataExtractor
- show_lightbox_dialog
- resolve_asset_path
- models.py
- temp_storage
- GeminiProvider
- backup_daily.sh
- run_pipeline.sh
- load_config
- OllamaProvider
- seed-synthesis-engine
- routers/style.py
- main.py
- auth.py
- LLMServiceError
- test_batch_extractor_job_tracking
- get_style_profile
- PactoryError
- llm_service_error_handler

## God Nodes (most connected - your core abstractions)
1. `StorageRepository` - 102 edges
2. `LLMClient` - 61 edges
3. `load_config()` - 49 edges
4. `ArticleArchetype` - 39 edges
5. `get_db()` - 36 edges
6. `SeedRoleAssignment` - 35 edges
7. `ArticleRecord` - 33 edges
8. `init_db()` - 33 edges
9. `LLMServiceError` - 31 edges
10. `ArticleMetadata` - 31 edges

## Surprising Connections (you probably didn't know these)
- `test_complementary_seed_selection()` --uses--> `ArticleArchetype`  [INFERRED]
  tests/test_retriever.py → src/models.py
- `distillation_env()` --uses--> `StorageRepository`  [INFERRED]
  tests/test_distiller.py → src/storage/repository.py
- `extraction_env()` --uses--> `StorageRepository`  [INFERRED]
  tests/test_extraction.py → src/storage/repository.py
- `repo()` --uses--> `StorageRepository`  [INFERRED]
  tests/test_jobs_and_creations.py → src/storage/repository.py
- `test_batch_extractor_job_tracking()` --uses--> `StorageRepository`  [INFERRED]
  tests/test_jobs_and_creations.py → src/storage/repository.py

## Import Cycles
- None detected.

## Communities (83 total, 51 thin omitted)

### Community 0 - "routers/editor.py"
Cohesion: 0.12
Nodes (13): delete_creation(), _extract_title_from_text(), get_creation(), list_creations(), proofread_draft(), save_creation(), update_creation(), CreationDetailResponse (+5 more)

### Community 1 - "routers/inbox.py"
Cohesion: 0.11
Nodes (14): cmd_ingest(), get_inbox_stats(), list_articles(), process_inbox(), scan_inbox(), ArticleListResponse, ArticleSummaryItem, InboxFileItem (+6 more)

### Community 2 - "BaseLLMProvider"
Cohesion: 0.13
Nodes (3): BaseLLMProvider, ClaudeProvider, _clean_and_parse_json()

### Community 3 - "routers/generator.py"
Cohesion: 0.19
Nodes (11): _build_seed_assignments(), generate_blueprint(), search_seed_candidates(), synthesize_draft(), BlueprintGenerateRequest, BlueprintGenerateResponse, DraftSynthesizeRequest, DraftSynthesizeResponse (+3 more)

### Community 4 - "llm_client.py"
Cohesion: 0.11
Nodes (4): reset_generator_state(), load_env_file(), UserStyleProfile, reset_generator_state()

### Community 5 - "StyleLearner"
Cohesion: 0.15
Nodes (3): get_services(), cmd_learn_style(), StyleLearner

### Community 6 - "ArticleArchetype"
Cohesion: 0.05
Nodes (20): ArticleArchetype, DistilledMaterialSheet, SeedRoleAssignment, SynthesisBlueprint, MaterialDistiller, SynthesisPlanner, ArticleSynthesizer, CleanYamlDumper (+12 more)

### Community 7 - "ArticleRecord"
Cohesion: 0.12
Nodes (10): ArticleMetadata, ArticleRecord, ArticleStatus, VisualAssetItem, test_fault_tolerant_checkpointing_resumption(), test_structured_metadata_extraction(), test_synthesizer_job_and_creation_recording(), test_article_crud() (+2 more)

### Community 8 - "paths"
Cohesion: 0.06
Nodes (34): core_problem, notable_episodes, reframing_logic, solution_framework, title, topic_tags, extraction, concurrency (+26 more)

### Community 9 - "config.py"
Cohesion: 0.17
Nodes (8): AppConfig, ExtractionSettings, PathSettings, RetrievalSettings, TaxonomySettings, extraction_env(), style_env(), synthesizer_env()

### Community 10 - "package.json"
Cohesion: 0.12
Nodes (21): @tailwindcss/vite@^4.3.4, devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6 (+13 more)

### Community 11 - "test_api.py"
Cohesion: 0.11
Nodes (8): test_auth_rejection_and_login(), test_creations_crud_lifecycle(), test_health_check(), test_inbox_endpoints(), test_observability_endpoint(), test_proofread_endpoint_mocked(), test_seed_search_endpoint(), test_style_endpoints()

### Community 12 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 13 - "client.ts"
Cohesion: 0.16
Nodes (15): lucide-react@^1.69.0, api, ArticleSummaryItem, CreationDetailResponse, CreationSummaryItem, DraftSynthesizeResponse, editorApi, inboxApi (+7 more)

### Community 14 - "StorageRepository"
Cohesion: 0.14
Nodes (3): VisualAssetManifest, StorageRepository, populated_retriever()

### Community 15 - "pactory-studio"
Cohesion: 0.12
Nodes (16): context, dockerfile, interval, retries, start_period, test, timeout, build (+8 more)

### Community 16 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "get_db"
Cohesion: 0.09
Nodes (3): get_connection(), get_db(), test_init_db_creates_tables()

### Community 18 - "App.tsx"
Cohesion: 0.23
Nodes (11): authApi, App(), AuthModal(), AuthModalProps, Navbar(), InboxPage(), LibraryPage(), StudioEditorPage() (+3 more)

### Community 19 - "Navbar.tsx"
Cohesion: 0.17
Nodes (13): BlueprintResponse, draftApi, observabilityApi, ObservabilityStats, SeedCandidateItem, NavbarProps, NavTab, ARCHETYPES (+5 more)

### Community 21 - ".select_complementary_seeds"
Cohesion: 0.15
Nodes (5): SeedRetriever, score_seed2(), get_services(), test_cosine_similarity(), test_jaccard_and_keyword_extraction()

### Community 22 - "scanner.py"
Cohesion: 0.10
Nodes (8): ImageFilterSettings, PDFProcessor, clean_boilerplate(), extract_author_and_date(), normalize_markdown(), create_sample_pdf_with_image(), test_10_sample_articles_ingestion(), test_boilerplate_stripping()

### Community 24 - "dependencies"
Cohesion: 0.20
Nodes (10): dependencies, axios@^1.21.0, react@^19.3.1, react-dom@^19.3.1, tailwindcss@^4.3.4, zustand@^5.0.16, axios, react-dom (+2 more)

### Community 26 - "ArticleProofreader"
Cohesion: 0.16
Nodes (6): ArticleProofreader, test_proofreader_async_review(), test_proofreader_raises_when_no_api_key(), test_proofreader_report_mode_with_mock(), test_proofreader_rewrite_mode_with_mock(), test_split_frontmatter()

### Community 27 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 29 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, lint, preview

### Community 56 - "models.py"
Cohesion: 0.12
Nodes (5): ReusableAssetType, init_db(), repo(), test_complementary_seed_selection(), test_style_learning_cycle()

### Community 58 - "GeminiProvider"
Cohesion: 0.15
Nodes (6): GeminiProvider, _call(), _call(), is_retryable_error(), retry_async(), retry_sync()

### Community 64 - "load_config"
Cohesion: 0.17
Nodes (6): cmd_generate(), cmd_init(), cmd_pipeline(), cmd_search(), cmd_ui(), load_config()

### Community 73 - "routers/style.py"
Cohesion: 0.24
Nodes (6): run_style_learning(), update_style_profile(), StyleLearnRequest, StyleLearnResponse, StyleProfileResponse, StyleUpdateRequest

### Community 74 - "main.py"
Cohesion: 0.16
Nodes (4): auth_status(), health_check(), root_placeholder(), serve_spa()

### Community 75 - "auth.py"
Cohesion: 0.22
Nodes (5): get_configured_password(), LoginRequest, LoginResponse, verify_auth(), login()

## Knowledge Gaps
- **1 isolated node(s):** `seed-synthesis-engine`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 441 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **51 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `StorageRepository` connect `StorageRepository` to `routers/editor.py`, `routers/inbox.py`, `routers/generator.py`, `llm_client.py`, `StyleLearner`, `ArticleArchetype`, `ArticleRecord`, `config.py`, `get_db`, `test_pipeline_job_lifecycle`, `.select_complementary_seeds`, `scanner.py`, `LLMClient`, `test_drafts_and_creations_workflow`, `get_observability_metrics`, `BatchMetadataExtractor`, `models.py`, `temp_storage`, `load_config`, `routers/style.py`, `.list_creations`, `test_batch_extractor_job_tracking`, `get_style_profile`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `StorageRepository` (e.g. with `delete_creation()` and `get_creation()`) actually correct?**
  _`StorageRepository` has 34 INFERRED edges - model-reasoned connections that need verification._
- **What connects `seed-synthesis-engine` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `routers/editor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12183908045977011 - nodes in this community are weakly interconnected._
- **Why does `LLMClient` connect `LLMClient` to `load_config`, `routers/editor.py`, `routers/inbox.py`, `routers/generator.py`, `llm_client.py`, `StyleLearner`, `OllamaProvider`, `ArticleArchetype`, `routers/style.py`, `config.py`, `BatchMetadataExtractor`, `.select_complementary_seeds`, `models.py`, `ArticleProofreader`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `LLMClient` (e.g. with `cmd_extract()` and `cmd_generate()`) actually correct?**
  _`LLMClient` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `routers/inbox.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10952380952380952 - nodes in this community are weakly interconnected._