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
  - [x] `prompts.py` — system prompt + one few-shot example per tool
  - [x] `schema.py` — per-tool filter schemas + strict `validate_planner_call()`
  - [x] `planner.py` — `Planner` class + `PlannerResult`
  - [x] `__init__.py` — public exports
- [x] Planner tests (`scripts/test_planner.py`)

## Current

- [ ] POST /chat endpoint with SSE streaming

## Next

- [ ] Chat interface (Next.js)

## Future

- [ ] File upload analysis
- [ ] Experiment comparison
- [ ] OpenAI provider (implement stub)
- [ ] Anthropic provider (implement stub)
- [ ] Gemini provider (implement stub)

## Not Yet

- [ ] Agents
- [ ] LangGraph
- [ ] Vector databases
- [ ] Fine-tuning

## Repository Workflow

- [x] GitHub remote: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- [ ] Commit and push each milestone to `origin/main`
- [ ] Avoid force pushes and history rewrites
