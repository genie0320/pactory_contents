# routers/generator.py

> 60 nodes · cohesion 0.06

## Key Concepts

- **routers/generator.py** (38 connections) — `src/api/routers/generator.py`
- **main.py** (27 connections) — `src/api/main.py`
- **auth.py** (16 connections) — `src/api/auth.py`
- **synthesize_draft()** (16 connections) — `src/api/routers/generator.py`
- **generate_blueprint()** (13 connections) — `src/api/routers/generator.py`
- **observability.py** (11 connections) — `src/api/routers/observability.py`
- **schemas/generator.py** (11 connections) — `src/api/schemas/generator.py`
- **search_seed_candidates()** (10 connections) — `src/api/routers/generator.py`
- **pydantic** (8 connections)
- **get_configured_password()** (8 connections) — `src/api/auth.py`
- **verify_auth()** (8 connections) — `src/api/auth.py`
- **_build_seed_assignments()** (8 connections) — `src/api/routers/generator.py`
- **fastapi** (7 connections)
- **BaseModel** (7 connections)
- **PactoryError** (7 connections) — `src/exceptions.py`
- **login()** (6 connections) — `src/api/main.py`
- **LoginRequest** (4 connections) — `src/api/auth.py`
- **LoginResponse** (4 connections) — `src/api/auth.py`
- **auth_status()** (4 connections) — `src/api/main.py`
- **llm_service_error_handler()** (4 connections) — `src/api/main.py`
- **pactory_error_handler()** (4 connections) — `src/api/main.py`
- **BlueprintGenerateRequest** (4 connections) — `src/api/schemas/generator.py`
- **BlueprintGenerateResponse** (4 connections) — `src/api/schemas/generator.py`
- **DraftSynthesizeRequest** (4 connections) — `src/api/schemas/generator.py`
- **DraftSynthesizeResponse** (4 connections) — `src/api/schemas/generator.py`
- *... and 35 more nodes in this community*

## Relationships

- [llm_client.py](llm_client.py.md) (21 shared connections)
- [LLMClient](LLMClient.md) (17 shared connections)
- [ArticleArchetype](ArticleArchetype.md) (11 shared connections)
- [StorageRepository](StorageRepository.md) (7 shared connections)
- [AppConfig](AppConfig.md) (6 shared connections)
- [routers/inbox.py](routers-inbox.py.md) (5 shared connections)
- [StyleLearner](StyleLearner.md) (5 shared connections)
- [LLMServiceError](LLMServiceError.md) (4 shared connections)
- [test_api.py](test_api.py.md) (3 shared connections)
- [.get_article](get_article.md) (1 shared connections)
- [.select_complementary_seeds](select_complementary_seeds.md) (1 shared connections)
- [DistilledMaterialSheet](DistilledMaterialSheet.md) (1 shared connections)

## Source Files

- `src/api/auth.py`
- `src/api/main.py`
- `src/api/routers/__init__.py`
- `src/api/routers/generator.py`
- `src/api/routers/observability.py`
- `src/api/schemas/generator.py`
- `src/exceptions.py`

## Audit Trail

- EXTRACTED: 158 (84%)
- INFERRED: 31 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*