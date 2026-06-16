# PROJECT STATE

Last Updated: 2026-06-16

## Current Phase

Phase 3 — Planner + Provider Layer

## Completed

- ORD dataset converted to JSONL
- Procedure database extracted
- Molecule registry built
- Dataset validation completed
- Dataset validation utility created at `scripts/validate_datasets.py`
- DuckDB schema created at `backend/database/schema.sql`
- DuckDB ingestion pipeline created at `scripts/ingest_duckdb.py`
- ORD datasets imported into `backend/database/ord.duckdb`
- DuckDB schema verified from the live database
- DuckDB-backed tool layer implemented in `backend/tools/`
- Smoke tests added at `scripts/test_tool_layer.py`
- FastAPI backend layer implemented in `backend/api/`
- API endpoint smoke tests added at `scripts/test_api_endpoints.py`
- Local API startup script added at `scripts/run_api.py`
- DuckDB-backed analytics tools implemented in `backend/tools/analytics_tools.py`
- Analytics validation tests added at `scripts/test_analytics_tools.py`
- Analytics example output script added at `scripts/example_analytics_outputs.py`
- Analytics API endpoints added to `backend/api/routes.py`
- Analytics API endpoint tests added at `scripts/test_analytics_endpoints.py`
- Analytics Pydantic models added to `backend/api/models.py`
- `requirements.txt` updated: added `pydantic==2.11.7` and `httpx==0.28.1`
- Provider abstraction layer implemented in `backend/providers/`
- Provider tests added at `scripts/test_providers.py`
- Planner layer implemented in `backend/planner/`
- Planner tests added at `scripts/test_planner.py` — 43 tests, all passing

Datasets:

- Reactions: 2,376,120
- Procedures: 1,788,170
- Molecules: 1,993,180

FastAPI backend (all endpoints):

- `GET /health`
- `GET /reactions/search`
- `GET /procedures/search`
- `GET /molecules/search`
- `GET /analytics/catalysts`
- `GET /analytics/yields`
- `GET /analytics/temperatures`
- `GET /analytics/datasets`
- `GET /analytics/reaction-types`
- `GET /analytics/summary`

Provider abstraction layer (`backend/providers/`):

- `base.py` — `BaseProvider` ABC, `Message`, `ChatResponse`, `GenerateResponse`
- `config.py` — `ProviderConfig` dataclass, `load_config()` from `ORD_*` env vars
- `ollama_provider.py` — live Ollama REST API implementation
- `openai_provider.py`, `anthropic_provider.py`, `gemini_provider.py` — documented stubs
- `provider_factory.py` — `get_provider()` registry factory
- `__init__.py` — clean public exports

Planner layer (`backend/planner/`):

- `prompts.py` — SYSTEM_PROMPT: full tool catalog, filter schemas, output format rules,
  one worked few-shot example per tool (9 examples total)
- `schema.py` — TOOL_FILTER_SCHEMAS, KNOWN_TOOLS, `validate_planner_call()`,
  `PlannerValidationError`
- `planner.py` — `Planner` class + `PlannerResult` dataclass:
  - Builds prompt → calls LLM → extracts JSON (brace-balanced scanner)
  - Validates with `validate_planner_call()` → dispatches to tool function
  - One retry with a correction prompt on parse/validation failure
  - Never raises — all failures are returned as `PlannerResult(success=False)`
- `__init__.py` — public exports

## Current Focus

- POST /chat endpoint with SSE streaming

## Next Milestones

1. POST /chat FastAPI endpoint with SSE streaming
2. Next.js chat interface (Phase 4)

## Infrastructure Status

Database: DuckDB created and populated

Backend: FastAPI retrieval and analytics API fully implemented

Providers: BaseProvider + OllamaProvider live, stubs for OpenAI/Anthropic/Gemini

Planner: Fully implemented — intent → DSL → validate → dispatch → result

Frontend: Not Started

## Repository Status

- Git is initialized for this workspace
- GitHub remote `origin` exists
- Repository: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
