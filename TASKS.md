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
- [x] Analytics API endpoints (`/analytics/catalysts`, `/analytics/yields`, `/analytics/temperatures`, `/analytics/datasets`, `/analytics/reaction-types`, `/analytics/summary`)
- [x] Analytics endpoint tests (`scripts/test_analytics_endpoints.py`)
- [x] Fix `requirements.txt` — added `pydantic` and `httpx`

## Current

- [ ] Ollama provider abstraction (`backend/providers/`)

## Next

- [ ] Planner (`backend/planner/planner.py`)
- [ ] POST /chat endpoint with SSE streaming
- [ ] Chat interface (Next.js)

## Future

- [ ] File upload analysis
- [ ] Experiment comparison
- [ ] OpenAI provider
- [ ] Anthropic provider
- [ ] Gemini provider

## Not Yet

- [ ] Agents
- [ ] LangGraph
- [ ] Vector databases
- [ ] Fine-tuning

## Repository Workflow

- [x] GitHub remote: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- [ ] Commit and push each milestone to `origin/main`
- [ ] Avoid force pushes and history rewrites
