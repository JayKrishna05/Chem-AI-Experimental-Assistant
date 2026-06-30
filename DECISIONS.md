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

## Database Strategy

Current database:

- DuckDB

Future compatibility:

- PostgreSQL support is expected.
- Future semantic search may use pgvector.

Architecture requirement:

- Business logic, planner logic, API contracts, and providers must not depend on a specific database implementation.

Guideline:

- New functionality should be implemented behind interfaces where practical.
- Avoid embedding DuckDB-specific behavior outside the data access layer.

Status:

Approved

## Backend

FastAPI

## Frontend

Next.js + Tailwind + shadcn/ui

## LLM Architecture

Provider abstraction.

Supported providers:
- Ollama (live)
- Groq (live — added 2026-06-23)
- OpenAI (stub)
- Anthropic (stub)
- Gemini (stub)

## Groq Provider

Groq uses an OpenAI-compatible REST API.

Implementation:
- `backend/providers/groq_provider.py` — live implementation via `urllib` (no new package dependencies)
- API key via `ORD_GROQ_API_KEY` environment variable
- Live `list_models()` calls Groq `/models`, filters non-chat models, falls back to static list
- Registered in `provider_factory._PROVIDER_REGISTRY` under key `"groq"`

Rationale:
- Groq provides very fast inference, making it ideal as a formatter with a slower local planner
- Recommended demo config: Planner=Ollama/qwen2.5:3b + Formatter=Groq/llama-3.3-70b-versatile

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

## Dual-Provider Architecture (decided 2026-06-23)

The planner and formatter must use independently instantiated provider objects.

Rationale:
- Planner can use a fast local model (low latency intent detection)
- Formatter can use a powerful cloud model (high quality summaries)
- Cross-provider routing was previously broken — a single shared instance was used for both roles

Implementation:
- `backend/api/state.py` stores 6 keys: `planner_provider`, `planner_model`, `planner_timeout`, `formatter_provider`, `formatter_model`, `formatter_timeout`
- `backend/chat/stream.py` instantiates two provider objects — reuses one instance only when both names are equal
- `backend/api/chat_routes.py` injects all 6 values from global state if not provided in request body
- Frontend POSTs all 6 values explicitly so UI state is the source of truth

Recommended demo configuration:
- Planner: Ollama / qwen2.5:3b (fast, local intent detection)
- Formatter: Groq / llama-3.3-70b-versatile (high quality, fast cloud inference)

## Architecture Audit Findings (2026-06-23)

A full execution path audit was performed. See `CHANGE_LOG.md` for complete details.

Key fixes applied:
- Stub providers (`OpenAI`, `Anthropic`, `Gemini`) were missing `list_models()` — would TypeError at instantiation
- `useChatStream` never sent model/provider in POST body — relied entirely on server global state
- `formatter.py` had internal `active_models` import (circular coupling) — removed
- `formatter_timeout` was shared for both planner and formatter — split into separate fields
- No `GET /providers` endpoint existed — added
- `GET /models` could only query the active planner provider — now accepts `?provider=` param

## Data Access Layer (DAL) Refactor (decided 2026-06-30)

All direct DuckDB SQL queries have been removed from the Tool layer and encapsulated into dedicated domain Repositories (`backend/database/repositories/`).

Rationale:
- To allow the `ComparisonService` to query database statistics without parsing UI-oriented tool contracts.
- To prevent test suite lock contention by centrally managing `read_only=True` connections via `BaseRepository`.
- To establish a scalable backend architecture that isolates business logic from database interactions, preparing the system for a future PostgreSQL migration (Phase 7).

Implementation:
- Created `ReactionRepository`, `ProcedureRepository`, and `StatisticsRepository`.
- Resolved circular imports by ensuring Repositories define their own Pydantic input models via `TYPE_CHECKING` instead of importing from `backend.tools.__init__`.

