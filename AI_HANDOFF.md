# AI HANDOFF

Date: 2026-06-26

## Current Status

Phase 6 Implementation: **Frontend Integration & User Experience** is complete.

The LLM Planner benchmark accuracy is stable at **59.0%**.

- **Phase 6 Frontend Integration**: Built a robust, modular frontend upload pipeline leveraging independent API services (`api.ts`, `upload.ts`, `chat.ts`). 
- **Upload UI Component**: `UploadDropzone.tsx`, `UploadPreview.tsx`, and `ComparisonResultCard.tsx` intelligently handle validation, state, and scientific rendering.
- **Workflow Automation**: Successfully coupled file uploads into the chat context; uploading automatically pushes the report into the conversation and prompts the assistant to provide an interpretation.
- **Backend Capability Check**: Integrated dynamic backend polling (`GET /system/capabilities`) to gracefully adjust upload support on the frontend.
- **Provider Initialization Resilience**: Missing provider configurations (e.g., missing API keys) now gracefully degrade by emitting an `available: false` status, preventing frontend startup crashes and presenting non-blocking UI warnings.
- **Phase 5 Pipeline Built**: Created an independent pipeline decoupling parsing, normalization, validation, and comparison into distinct modules. `POST /experiments/compare` integrates these into the existing Tool/DuckDB layer.
- **Backend Packages Added**: Introduced `backend/experiment` (models, parsers, normalizers, validators) and `backend/services` (comparison).
- **Documentation Consolidation**: All architecture reports and validation metrics are up to date.

## 3. Architecture Constraints

1.  **Strict Phase Discipline**: Do NOT build features for future phases (like Semantic Search or PostgreSQL) until the current phase is fully stabilized and closed out.
2.  **No `pandas`**: We use DuckDB for all data manipulation.
3.  **One Orchestrator Pattern**: Do not add new planner layers. The FastAPI backend contains a single `Planner` (in `planner.py`) and a single `Formatter`. Use `tool_result_override` in the `ChatRequest` to bypass the planner for direct summarization tasks (like upload reports).
4.  **Graceful Degradation**: Always check for `providerStatus` (e.g., if Groq fails due to an API key issue, the system must continue to function on Ollama without raising a fatal 500 error).
5.  **Environment Variables**: `load_dotenv()` is injected at the very top of `backend/api/main.py`. Do not duplicate it into individual provider modules.

## 4. Current State
We have completed **Phase 6 (Frontend Integration)**. The upload pipeline is robust and integrates natively into the Next.js chat interface. The system leverages `tool_result_override` to feed upload results directly to the LLM formatter.

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
Dataset  →  DuckDB  →  Tools (10 tools)  →  FastAPI
                                          ↓
Upload (CSV/JSON) → Parser → Normalizer → Comparison Service
```

Recommended testing configuration:
```
Planner:   Ollama  /  qwen2.5:3b               (fast local intent detection)
Formatter: Groq    /  llama-3.3-70b-versatile  (fast cloud, high quality)
```

The Phase 6 Frontend Integration is live. The platform is now fully capable of allowing users to upload chemistry experiments and interact natively with their comparison analysis within the chat stream.

Your next objective is to transition from local analytics to scalable persistence:

1. **Phase 7: PostgreSQL Migration**: Begin designing the PostgreSQL schema to persist user-uploaded `CanonicalExperiment` objects.
2. **Data Access Layer (DAL)**: Extract the DuckDB SQL logic from `backend/tools/analytics_tools.py` into a new `backend/database/repositories/` layer. Both the UI tools and the `ComparisonService` must call this repo layer.
3. **Provenance & Typing**: Implement `EvidenceBundle` inside a typed `ComparisonResult` model (see `comparison_result_design.md` and `provenance_design.md`).
4. **Catalyst Normalization Table**: Create a table/view in DuckDB (`ord.duckdb`) to collapse catalyst synonyms.

## Rules

- **Use DuckDB** for all data access currently. No Vector DBs or external graphs should be used for the MVP.
- **Preserve chemistry JSON structures**
- **Read `PROJECT_STRUCTURE.md`** before making any architectural or file modifications.
- **Update documentation** (`PROJECT_STATE.md`, `TASKS.md`, `AI_HANDOFF.md`, `CHANGE_LOG.md`) after major milestones.
