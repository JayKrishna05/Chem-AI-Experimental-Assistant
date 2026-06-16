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

## Current

- [x] Pre-Phase 5 Audit & Stabilization complete

## Next

- [ ] File upload UI support
- [ ] Experiment comparison engine (Phase 5)
- [ ] OpenAI provider (implement stub)
- [ ] Anthropic provider (implement stub)
- [ ] Gemini provider (implement stub)
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
