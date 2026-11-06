# test_api.py

> 21 nodes · cohesion 0.10

## Key Concepts

- **test_api.py** (17 connections) — `tests/test_api.py`
- **unittest_mock** (4 connections)
- **test_proofread_endpoint_mocked()** (3 connections) — `tests/test_api.py`
- **test_auth_rejection_and_login()** (2 connections) — `tests/test_api.py`
- **test_creations_crud_lifecycle()** (2 connections) — `tests/test_api.py`
- **test_health_check()** (2 connections) — `tests/test_api.py`
- **test_inbox_endpoints()** (2 connections) — `tests/test_api.py`
- **test_observability_endpoint()** (2 connections) — `tests/test_api.py`
- **test_seed_search_endpoint()** (2 connections) — `tests/test_api.py`
- **test_style_endpoints()** (2 connections) — `tests/test_api.py`
- **fastapi_testclient** (1 connections)
- **patch** (1 connections)
- **Integration tests for Pactory Studio FastAPI REST API.** (1 connections) — `tests/test_api.py`
- **Verify style profile retrieval.** (1 connections) — `tests/test_api.py`
- **Verify proofreading endpoint with mocked LLM review.** (1 connections) — `tests/test_api.py`
- **Verify healthcheck endpoint returns 200 OK without auth.** (1 connections) — `tests/test_api.py`
- **Verify observability stats endpoint returns aggregated metric keys.** (1 connections) — `tests/test_api.py`
- **Verify auth rejection when password is required, and successful login.** (1 connections) — `tests/test_api.py`
- **Verify inbox scan, stats, and articles endpoints.** (1 connections) — `tests/test_api.py`
- **Verify draft seed candidate search.** (1 connections) — `tests/test_api.py`
- **Verify full CRUD lifecycle for draft creations.** (1 connections) — `tests/test_api.py`

## Relationships

- [ArticleArchetype](ArticleArchetype.md) (3 shared connections)
- [routers/generator.py](routers-generator.py.md) (3 shared connections)
- [llm_client.py](llm_client.py.md) (2 shared connections)
- [LLMClient](LLMClient.md) (1 shared connections)

## Source Files

- `tests/test_api.py`

## Audit Trail

- EXTRACTED: 29 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*