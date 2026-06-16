# PROJECT STATE

Last Updated: 2026-06-17

## Current Phase

Phase 4 Complete — Pre-Phase 5 Capability Audit & Stabilization Complete

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
- Chat endpoint robustness improvements (payload truncation, formatter timeout, `formatting` event) implemented
- Chat endpoint smoke tests added at `scripts/test_chat_endpoint.py`
- **Next.js 15 Frontend Chat Interface** completed with tailwindcss and shadcn/ui.
- `useChatStream` hook implemented for parsing the SSE stream and managing state.
- `ChatInterface`, `ChatStream`, `ChatMessage`, `ChatInput` components added.
- `ToolResultCard` added to display raw JSON payloads seamlessly.
- **Backend JSON Sanitization** implemented. `NaN` and `Infinity` from DuckDB analytics are recursively cleaned to `null` to ensure RFC-compliant JSON parsing on the frontend.
- **Model Management**: Added `GET /models`, `GET /models/current`, and `POST /models/current` to allow dynamic model selection.
- **Frontend Model Switcher**: Added Planner and Formatter model dropdowns directly into `ChatInterface.tsx` header for rapid testing.
- **Timeout Propagation**: `formatter_timeout` flows from UI → API state → stream.py → planner.py → formatter.py → OllamaProvider → urlopen, fully end-to-end.
- **Formatter Robustness**: `format_response()` catches all exceptions and returns a fallback summary so chat is never broken.
- **Pre-Phase 5 Capability Audit**: Executed comprehensive 100-question audit across all 15 categories. Score: 87/93 = 93.5%.
- **Clean Statistics**: `yield_statistics` and `temperature_statistics` now return both raw stats and `clean_statistics` (valid range only) to handle ORD data quality issues.
- **Reagent Statistics Tool**: New `reagent_statistics` analytics tool for solvent/reagent frequency analysis.
- **Expanded Planner Prompt**: Revised with 35+ examples, IMPORTANT NOTES about NULL reaction_type prevalence, SMILES mapping for named molecules, and all new tool coverage.
- **Empty State UI**: `ChatStream` now shows 10 clickable suggestion chips on the empty state that immediately dispatch queries.
- **Comprehensive Audit Tests**: Added `scripts/test_audit.py` covering 45 automated assertions.

## Critical Database Facts (discovered during audit)

- **99.97% of reactions (2,375,370 / 2,376,120) have `reaction_type = NULL`**
  - Only 750 reactions have a type label (all Buchwald-Hartwig variants)
  - Searches for "Suzuki", "Heck", "amide coupling" by reaction_type return 0 results
  - This is an ORD dataset characteristic, not a system bug
- **Yield data contains extreme outliers** (up to 9×10¹⁹%)
  - clean_statistics (0-100% range): avg=63.83%, med=68.30%
- **Temperature data: 81% of records at or below 0°C** (likely default values)
  - clean_statistics (-100°C to 300°C): avg=13.63°C, med=0°C
- **Molecule registry contains SMILES only** — no compound names
  - Ethanol (CCO): 40,408 occurrences. Acetone (CC(C)=O): 8,364. Benzene (c1ccccc1): 5,331.

Datasets:

- Reactions: 2,376,120
- Procedures: 1,788,170
- Molecules: 1,993,180
- Source Datasets: 542

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
- `GET /models`
- `GET /models/current`
- `POST /models/current`
- **`POST /chat`** (SSE streaming endpoint)

Chat & Formatting Layer (`backend/chat/`):

- `stream.py` — Orchestrates Planner -> LLM summary -> SSE event yielding.
- `formatter.py` — LLM-powered response formatter that translates raw JSON output into a conversational summary. Includes try/except fallback.
- Ensures absolute database-independence above the tool layer, enabling future pgvector/vss additions seamlessly.

Provider abstraction layer (`backend/providers/`):

- `base.py` — `BaseProvider` ABC, `Message`, `ChatResponse`, `GenerateResponse`
- `config.py` — `ProviderConfig` dataclass, `load_config()` from `ORD_*` env vars
- `ollama_provider.py` — live Ollama REST API implementation with configurable timeout
- `provider_factory.py` — `get_provider()` registry factory
- Stubs for OpenAI/Anthropic/Gemini.

Planner layer (`backend/planner/`):

- `prompts.py` — SYSTEM_PROMPT: full tool catalog with 10 tools, IMPORTANT NOTES about database characteristics, 35+ worked examples.
- `schema.py` — Strict `validate_planner_call()` with `reagent_statistics` support.
- `planner.py` — `Planner` class: builds prompt → LLM → JSON extraction → validation → tool dispatch.

Tools layer (`backend/tools/`):

- `chemistry_tools.py` — `search_reactions`, `search_procedures`, `molecule_lookup`
- `analytics_tools.py` — `catalyst_statistics`, `yield_statistics` (with clean_statistics), `temperature_statistics` (with clean_statistics), `source_dataset_statistics`, `reaction_type_statistics`, `reagent_statistics`, `dataset_summary`

## Current Focus

- Begin Phase 5: Experiment comparison engine and file upload workflow

## Next Milestones

1. File upload workflow in frontend.
2. Experiment comparison engine backend implementation.
3. OpenAI/Anthropic/Gemini stub implementations.
4. Molecule name → SMILES lookup table for common compounds.
5. Solvent analytics improvements (per-dataset reagent breakdown).
6. Mobile header layout improvement.

## Infrastructure Status

Database: DuckDB created and populated. (Future compatibility with Postgres/pgvector documented and preserved).

Backend: FastAPI retrieval, analytics, and streaming chat API fully implemented.

Providers: BaseProvider + OllamaProvider live (with configurable timeout), stubs for OpenAI/Anthropic/Gemini.

Planner: Fully implemented — intent → DSL → validate → dispatch → result. 10 tools registered.

Frontend: Phase 4 completed (Next.js chat interface with suggestions, copy buttons, model switcher, timeout control).

Audit: 93.5% pass rate (87/93 tests). 6 structural failures due to ORD dataset characteristics (NULL reaction_type).

## Repository Status

- Git is initialized for this workspace
- GitHub remote `origin` exists
- Repository: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
