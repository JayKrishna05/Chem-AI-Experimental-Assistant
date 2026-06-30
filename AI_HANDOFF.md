# AI HANDOFF

Date: 2026-06-26

## Current Status

Phase 6.5 Implementation: **Data Access Layer & Scientific Correctness** is complete.

The LLM Planner benchmark accuracy is stable at **59.0%**.

- **Data Access Layer (DAL):** All raw DuckDB SQL is now centralized in `backend/database/repositories/` which cleanly isolates the business logic layer.
- **Scientific Correctness:** `ComparisonService` now employs hierarchical similarity matching and provides complete `EvidenceBundle` provenances for all comparisons.
- **Test Suite Resiliency:** Broken circular imports and DuckDB concurrency test locks were resolved. Python benchmarks have been established in `tests/benchmarks/`.
- **Phase 6 Frontend Integration**: Built a robust, modular frontend upload pipeline leveraging independent API services (`api.ts`, `upload.ts`, `chat.ts`). 
- **Workflow Automation**: Successfully coupled file uploads into the chat context; uploading automatically pushes the report into the conversation and prompts the assistant to provide an interpretation.
- **Provider Initialization Resilience**: Missing provider configurations (e.g., missing API keys) now gracefully degrade by emitting an `available: false` status, preventing frontend startup crashes and presenting non-blocking UI warnings.

## 3. Architecture Constraints

1.  **Strict Phase Discipline**: Do NOT build features for future phases (like Semantic Search or PostgreSQL) until the current phase is fully stabilized and closed out.
2.  **No `pandas`**: We use DuckDB for all data manipulation.
3.  **One Orchestrator Pattern**: Do not add new planner layers. The FastAPI backend contains a single `Planner` (in `planner.py`) and a single `Formatter`. Use `tool_result_override` in the `ChatRequest` to bypass the planner for direct summarization tasks (like upload reports).
4.  **Graceful Degradation**: Always check for `providerStatus` (e.g., if Groq fails due to an API key issue, the system must continue to function on Ollama without raising a fatal 500 error).
5.  **Environment Variables**: `load_dotenv()` is injected at the very top of `backend/api/main.py`. Do not duplicate it into individual provider modules.

## 4. Current State
We have completed **Phase 6.5 (Scientific Correctness & DAL)**. The backend now strictly separates Database logic (Repositories), Business Logic (`ComparisonService`), and Tool interfaces. The frontend upload pipeline seamlessly injects structured comparison results into the LLM context.

## Critical Database Facts (MUST READ)

> **99.97% of reactions have `reaction_type = NULL`**
> - The planner handles this: uses catalyst/reactant filters instead for those reaction types. This is an ORD dataset characteristic.

> **Yield data has extreme outliers**
> - `clean_statistics` (0-100% range): avg=63.83%, med=68.30% ← **use this**

> **Temperature data: 81% of records at or below 0°C**
> - `clean_statistics` (-100°C to 300°C): avg=13.63°C ← **use this**

> **Molecule registry is SMILES-only** — no compound names.

> **Catalyst identifiers are deeply fragmented**
> - Over 11k reactions lack SMILES strings for catalysts. A canonicalization mapping table is required for perfect similarity matches.

## Architecture & Configuration

```
Dataset  →  DuckDB  →  Repositories  →  Tools (13 tools)  →  FastAPI
                                  ↓
Upload (CSV/JSON) → Parser → Normalizer → Comparison Service
```

Recommended testing configuration:
```
Planner:   Ollama  /  qwen2.5:3b               (fast local intent detection)
Formatter: Groq    /  llama-3.3-70b-versatile  (fast cloud, high quality)
```

The Phase 6.5 Data Access Layer refactor is live. The platform is now fully capable of allowing users to upload chemistry experiments, dynamically match against the repository layer using hierarchical constraints, and evaluate results natively within the chat stream.

Your next objective is to transition from local analytics to scalable persistence:

1. **Phase 7: PostgreSQL Migration**: Begin designing the PostgreSQL schema to persist user-uploaded `CanonicalExperiment` objects.
2. **Catalyst Normalization Table**: Create a table/view in DuckDB (`ord.duckdb`) to collapse catalyst synonyms.

## Rules

- **Use DuckDB** for all data access currently. No Vector DBs or external graphs should be used for the MVP.
- **Preserve chemistry JSON structures**
- **Read `PROJECT_STRUCTURE.md`** before making any architectural or file modifications.
- **Update documentation** (`PROJECT_STATE.md`, `TASKS.md`, `AI_HANDOFF.md`, `CHANGE_LOG.md`) after major milestones.
