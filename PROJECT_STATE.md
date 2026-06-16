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

Datasets:

- Reactions: 2,376,120
- Procedures: 1,788,170
- Molecules: 1,993,180

DuckDB import:

- Database path: `backend/database/ord.duckdb`
- Imported rows verified and match expected counts
- Chemistry structures stored as DuckDB `JSON` columns
- `ingestion_audit` records source paths, expected counts, and imported counts

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

Provider abstraction layer:

- `backend/providers/base.py` — `BaseProvider` ABC, `Message`, `ChatResponse`, `GenerateResponse`
- `backend/providers/config.py` — `ProviderConfig` dataclass, `load_config()` from `ORD_*` env vars
- `backend/providers/ollama_provider.py` — live Ollama REST API implementation (stdlib urllib, no extra dep)
- `backend/providers/openai_provider.py` — documented stub (raises `NotImplementedError`)
- `backend/providers/anthropic_provider.py` — documented stub (raises `NotImplementedError`)
- `backend/providers/gemini_provider.py` — documented stub (raises `NotImplementedError`)
- `backend/providers/provider_factory.py` — `get_provider()` registry factory, `SUPPORTED_PROVIDERS`
- `backend/providers/__init__.py` — clean public exports (concrete classes not re-exported)

Configuration (environment variables):

- `ORD_PROVIDER` — active provider (`ollama` default)
- `ORD_PLANNER_MODEL` — planner model (`qwen2.5:3b` default)
- `ORD_ANALYSIS_MODEL` — analysis model (falls back to `ORD_PLANNER_MODEL`)
- `ORD_OLLAMA_BASE_URL` — Ollama server URL (`http://localhost:11434` default)
- `ORD_OPENAI_API_KEY` — OpenAI key (for future stub)
- `ORD_ANTHROPIC_API_KEY` — Anthropic key (for future stub)
- `ORD_GEMINI_API_KEY` — Gemini key (for future stub)

Live integration test:

- Ollama is running locally with `qwen2.5:3b`
- All 27 provider tests pass (including live chat and generate round-trips)

Analytics notes:

- `yield_statistics(reaction_type="Suzuki")` returns zero procedure records — normalized procedure reaction types in this dataset do not include Suzuki

## Current Focus

- Build the planner layer

## Next Milestones

1. Planner (`backend/planner/planner.py`)
2. POST /chat endpoint with SSE streaming
3. Chat interface (Next.js)

## Infrastructure Status

Database: DuckDB created and populated

Backend: FastAPI retrieval and analytics API fully implemented

Providers: BaseProvider + OllamaProvider live, stubs for OpenAI/Anthropic/Gemini

Frontend: Not Started

Planner: Not Started

## Repository Status

- Git is initialized for this workspace
- GitHub remote `origin` exists
- Repository: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
