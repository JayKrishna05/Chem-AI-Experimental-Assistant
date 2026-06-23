# TASKS

## Done

- [x] Convert ORD dataset
- [x] Extract procedures
- [x] Build molecule registry
- [x] Validate datasets
- [x] Dataset validation utility
- [x] DuckDB schema
- [x] Ingestion pipeline
- [x] Import ORD datasets into `backend/database/ord.duckdb`
- [x] Initialize Git repository
- [x] Configure GitHub remote
- [x] Verify live DuckDB schema
- [x] Reaction search tool
- [x] Procedure search tool
- [x] Molecule lookup
- [x] Tool layer smoke tests
- [x] FastAPI backend retrieval layer
- [x] API endpoint smoke tests
- [x] Simple local API startup script
- [x] Analytics tools
- [x] Analytics validation tests
- [x] Analytics example outputs
- [x] Analytics API endpoints
- [x] Analytics endpoint tests
- [x] Fix `requirements.txt` — added `pydantic` and `httpx`
- [x] Provider abstraction layer (`backend/providers/`)
- [x] Provider tests (`scripts/test_providers.py`)
- [x] Planner layer (`backend/planner/`)
  - [x] `prompts.py` — system prompt + worked few-shot examples per tool (35+)
  - [x] `schema.py` — per-tool filter schemas + strict `validate_planner_call()`
  - [x] `planner.py` — `Planner` class + `PlannerResult`
  - [x] `__init__.py` — public exports
- [x] Planner tests (`scripts/test_planner.py`)
- [x] POST /chat endpoint with SSE streaming (`backend/chat/` + `backend/api/chat_routes.py`)
- [x] Chat robustness improvements (truncation, formatting event, timeouts)
- [x] Chat interface (Next.js)
- [x] Model management API (`GET /models`, `GET /models/current`, `POST /models/current`)
- [x] Frontend model switcher (planner + formatter dropdowns)
- [x] Timeout propagation end-to-end (UI → API state → planner → formatter → urlopen)
- [x] Formatter robustness (try/except + graceful fallback)
- [x] Backend JSON sanitization (`backend/utils.py`)
- [x] **Comprehensive capability audit** (100-question, 15 categories, 93.5% pass rate)
- [x] `yield_statistics` — added `clean_statistics` (0-100% range) for valid yields
- [x] `temperature_statistics` — added `clean_statistics` (-100°C to 300°C) for valid temps
- [x] `reagent_statistics` — new tool for solvent/reagent analytics
- [x] Expanded planner prompt with 35+ examples and IMPORTANT NOTES
- [x] `ChatStream` empty-state with 10 clickable suggestion chips
- [x] `scripts/test_audit.py` — 45 automated assertions across all categories
- [x] **Architecture Audit (2026-06-23)** — full execution path trace, 8 bugs/gaps identified
- [x] Fix stub providers: `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider` — add `list_models()` and `timeout` params
- [x] Add `groq_api_key` to `ProviderConfig` + `load_config()` (`ORD_GROQ_API_KEY` env var)
- [x] **Groq Provider** — `backend/providers/groq_provider.py` (live, full implementation)
- [x] Register Groq in `provider_factory.py` registry
- [x] Expand `backend/api/state.py` — add `planner_provider`, `planner_timeout`, `formatter_provider`
- [x] Expand `backend/api/models.py` — `ChatRequest`, `CurrentModelsResponse`, `SetModelsRequest` carry all 6 fields
- [x] Rewrite `backend/api/chat_routes.py` — inject all 6 fields from state; new `GET /providers` endpoint; provider validation
- [x] Rewrite `backend/chat/stream.py` — **independent planner + formatter provider instances**; separate timeouts
- [x] Clean up `backend/chat/formatter.py` — remove internal `active_models` import
- [x] Update `frontend/src/types/chat.ts` — `CurrentModelsResponse` (6 fields), `ProvidersResponse`, `SetModelsRequest`
- [x] Rewrite `frontend/src/hooks/useModels.ts` — fetches `/providers`, caches models per-provider, separate state per role
- [x] Rewrite `frontend/src/hooks/useChatStream.ts` — `configRef` + `updateStreamConfig()`; POST body includes all 6 fields

## Current

- [/] Architecture Audit + Groq + Dual-Provider Switching
  - [x] Backend changes complete
  - [x] Frontend hooks/types complete
  - [ ] `ChatInterface.tsx` — add Provider dropdowns for each role
  - [ ] Live verification (backend startup + cross-provider test)
  - [ ] Commit + push

## Next

- [ ] `ChatInterface.tsx` — Planner Provider + Planner Model + Formatter Provider + Formatter Model selectors
- [ ] File upload UI support
- [ ] Experiment comparison engine (Phase 5)
- [ ] OpenAI provider — full implementation (not just stub)
- [ ] Anthropic provider — full implementation
- [ ] Gemini provider — full implementation
- [ ] Molecule name → SMILES lookup table for common compounds
- [ ] Mobile header layout improvement

## Future

- [ ] Semantic Search (pgvector or DuckDB VSS)
- [ ] PostgreSQL migration for operational database
- [ ] Per-dataset average yield and temperature analytics

## Not Yet

- [ ] Agents
- [ ] LangGraph
- [ ] Fine-tuning

## Repository Workflow

- [x] GitHub remote: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- [ ] Commit and push each milestone to `origin/main`
- [ ] Avoid force pushes and history rewrites
