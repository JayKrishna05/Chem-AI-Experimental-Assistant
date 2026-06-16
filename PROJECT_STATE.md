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

## Current Focus

- Build analytics tools on top of DuckDB

## Next Milestones

1. Analytics tools
2. FastAPI backend
3. Ollama planner
4. Chat interface

## Infrastructure Status

Database: DuckDB created and populated

Backend: Not Started

Frontend: Not Started

Planner: Not Started

Analytics: Not Started

## Repository Status

- Git is initialized for this workspace
- GitHub remote `origin` exists
- Repository: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
