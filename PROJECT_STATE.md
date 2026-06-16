# PROJECT STATE

Last Updated: 2026-06-16

## Current Phase

Foundation Setup

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

Datasets:

- Reactions: 2,376,120
- Procedures: 1,788,170
- Molecules: 1,993,180

Validation findings:

- `dataset/ord_jsonl_v1`: 24 JSONL shards, 2,376,120 counted records
- `dataset/ord_procedures_v1`: 18 JSONL shards, 1,788,170 counted records
- `dataset/molecule_registry_v1`: 1 JSONL file, 1,993,180 counted records
- Metadata counts match expected counts for all datasets

DuckDB import:

- Database path: `backend/database/ord.duckdb`
- Imported rows:
  - `reactions`: 2,376,120
  - `procedures`: 1,788,170
  - `molecules`: 1,993,180
- Chemistry structures are stored in DuckDB `JSON` columns
- `ingestion_audit` records source paths, expected counts, and imported counts

Schema verification:

- Tables present: `reactions`, `procedures`, `molecules`, `ingestion_audit`
- `reactions` JSON columns verified: `reactants_json`, `reagents_json`, `catalysts_json`, `products_json`, `conditions_json`
- `procedures` scalar columns verified: `reaction_id`, `reaction_type`, `temperature_c`, `yield_percent`, `procedure_text`
- `molecules` scalar columns verified: `smiles`, `occurrences`

Tool layer:

- `search_reactions()` supports scalar filters and JSON text filters for reactants, reagents, catalysts, and products
- `search_procedures()` supports reaction filters, procedure text search, temperature bounds, and yield bounds
- `molecule_lookup()` supports exact SMILES lookup, substring query, minimum occurrence filter, and result limiting

FastAPI backend:

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
- API routes call the existing DuckDB tool layer rather than duplicating query logic
- Typed request and response models live in `backend/api/models.py`
- Local startup: `python scripts/run_api.py`

Analytics tools:

- `catalyst_statistics()` ranks catalyst entries from `reactions.catalysts_json`
- `yield_statistics()` summarizes finite `procedures.yield_percent` values and reports out-of-range yield counts
- `temperature_statistics()` summarizes finite `procedures.temperature_c` values
- `source_dataset_statistics()` reports reaction/procedure/yield/temperature coverage by source dataset
- `reaction_type_statistics()` reports reaction/procedure/yield/temperature coverage by reaction type
- `dataset_summary()` reports chemistry coverage and dataset-level counts
- Each analytics function returns structured results with documented assumptions
- Validation tests compare analytics outputs against direct DuckDB queries
- `yield_statistics(reaction_type="Suzuki")` currently returns zero matching procedure records because the normalized procedure reaction types in this dataset do not include Suzuki

## Current Focus

- Prepare planner/provider layer while keeping tool execution explicit and DuckDB-backed

## Next Milestones

1. Ollama provider abstraction (`backend/providers/`)
2. Planner (`backend/planner/planner.py`)
3. POST /chat endpoint with SSE streaming
4. Chat interface (Next.js)

## Infrastructure Status

Database: DuckDB created and populated

Backend: FastAPI retrieval and analytics API fully implemented

Frontend: Not Started

Planner: Not Started

Providers: Not Started

Analytics: DuckDB chemistry analytics implemented and exposed via HTTP

## Repository Status

- Git is initialized for this workspace
- GitHub remote `origin` exists
- Repository: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
