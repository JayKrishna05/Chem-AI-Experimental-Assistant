# PROJECT STATE

Last Updated: 2026-06-16

## Current Phase

Phase 4 — Frontend Chat Interface

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
- Provider abstraction layer implemented in `backend/providers/`
- Provider tests added at `scripts/test_providers.py`
- Planner layer implemented in `backend/planner/`
- Planner tests added at `scripts/test_planner.py`
- **POST /chat endpoint with SSE streaming** implemented in `backend/chat/` and `backend/api/chat_routes.py`
- Chat endpoint smoke tests added at `scripts/test_chat_endpoint.py`

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
- **`POST /chat`** (SSE streaming endpoint)

Chat & Formatting Layer (`backend/chat/`):

- `stream.py` — Orchestrates Planner -> LLM summary -> SSE event yielding.
- `formatter.py` — LLM-powered response formatter that translates raw JSON output into a conversational summary.
- Ensures absolute database-independence above the tool layer, enabling future pgvector/vss additions seamlessly.

Provider abstraction layer (`backend/providers/`):

- `base.py` — `BaseProvider` ABC, `Message`, `ChatResponse`, `GenerateResponse`
- `config.py` — `ProviderConfig` dataclass, `load_config()` from `ORD_*` env vars
- `ollama_provider.py` — live Ollama REST API implementation
- `provider_factory.py` — `get_provider()` registry factory
- Stubs for OpenAI/Anthropic/Gemini.

Planner layer (`backend/planner/`):

- `prompts.py` — SYSTEM_PROMPT: full tool catalog, filter schemas, output format rules, one worked few-shot example per tool (9 examples total).
- `schema.py` — Strict `validate_planner_call()`.
- `planner.py` — `Planner` class: builds prompt → LLM → JSON extraction → validation → tool dispatch.

## Current Focus

- Next.js chat interface (Phase 4)

## Next Milestones

1. Initialize Next.js project.
2. Build chat UI consuming the `POST /chat` SSE stream.
3. Add specialized React cards for rendering `tool_result` data.

## Infrastructure Status

Database: DuckDB created and populated. (Future compatibility with Postgres/pgvector documented and preserved).

Backend: FastAPI retrieval, analytics, and streaming chat API fully implemented.

Providers: BaseProvider + OllamaProvider live, stubs for OpenAI/Anthropic/Gemini.

Planner: Fully implemented — intent → DSL → validate → dispatch → result.

Frontend: Not Started.

## Repository Status

- Git is initialized for this workspace
- GitHub remote `origin` exists
- Repository: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
