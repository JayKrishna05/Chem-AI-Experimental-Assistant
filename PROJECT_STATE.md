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

## Current Focus

- Build first DuckDB-backed search tools

## Next Milestones

1. Reaction search tool
2. Procedure search tool
3. Molecule lookup
4. FastAPI backend
5. Ollama planner
6. Chat interface

## Infrastructure Status

Database: DuckDB created and populated

Backend: Not Started

Frontend: Not Started

Planner: Not Started

Analytics: Not Started
