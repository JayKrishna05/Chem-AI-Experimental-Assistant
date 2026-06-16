# DECISIONS

## Dataset

Use existing converted datasets as source of truth.

Do Not:
- Re-download ORD
- Reconvert ORD

## Database

DuckDB

Reason:
Large local analytical workload.

Implementation:

- Primary local database is `backend/database/ord.duckdb`
- Schema is defined in `backend/database/schema.sql`
- Ingestion is performed by `scripts/ingest_duckdb.py`
- The ingestion script validates datasets before importing
- Existing databases are not overwritten unless `--replace` is passed

## Backend

FastAPI

## Frontend

Next.js + Tailwind + shadcn/ui

## LLM Architecture

Provider abstraction.

Supported providers:
- Ollama
- OpenAI
- Anthropic
- Gemini

## Default Model

Ollama + qwen2.5:3b

## Planner Architecture

Planner + Tools

No autonomous agents for MVP.

## Search Strategy

DuckDB retrieval first.

Vector databases only after MVP is complete.

## Chemistry Data

Preserve JSON structures.

Do not aggressively flatten:
- reactants
- reagents
- catalysts
- products
- conditions

DuckDB storage decision:

- Store chemistry arrays/objects as DuckDB `JSON` columns
- Extract stable scalar fields into typed columns for filtering and indexing
- Keep procedure text as `VARCHAR`
- Keep molecule occurrences as `BIGINT`

## Assumptions

- The existing `dataset/` directory is the source of truth
- JSONL files are newline-delimited and can be streamed by DuckDB `read_json`
- Procedure records are stored in a single `procedures` table using the fields specified in `PROJECT_SPEC.md`
- Generated DuckDB files are rebuildable from the source JSONL datasets

## Repository Workflow

- Git is initialized in the project workspace
- GitHub remote `origin` points to https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
