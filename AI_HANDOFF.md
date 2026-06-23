# AI HANDOFF

Date: 2026-06-23

## Current Status

Phase 5 Planning & Architecture Design complete. Transitioning to **Phase 5 Implementation: Experiment Upload & Comparison Engine.**

The LLM Planner benchmark accuracy is currently **58.0%**.

## What Changed This Session

- **Benchmark Improvements**: Added three massive new tools (`compare_datasets`, `top_yield_conditions`, `dataset_quality_report`) which jumped the planner's accuracy from 47.0% to 58.0% and resolved critical Comparative Chemistry failures.
- **Catalyst Identifier Audit**: Queried DuckDB and confirmed that catalyst names are wildly inconsistent. Over 11k reactions lack SMILES strings for catalysts, and synonyms like "Pd/C" map to dozens of different string hashes. **A `catalyst_normalization` table must be built before `compare_catalysts` is implemented.**
- **Architectural Reports**:
  - `remaining_failures_report.md`: Identified that 25 of the remaining 42 benchmark failures are explicitly waiting on Phase 5 workflows.
  - `phase5_capability_audit.md`: Outlined that implementing Phase 5 will solve ~25 benchmark failures.
  - `experiment_comparison_design.md`: Documented the Phase 5 schema, pipeline, similarity strategy, and MVP.
- **Codebase Cataloging**: Created `PROJECT_STRUCTURE.md`, an exhaustive map of the repository, request pipelines, and technical debt.

## Critical Database Facts (MUST READ)

> **99.97% of reactions have `reaction_type = NULL`**
> - Only 750 reactions have a type label (all Buchwald-Hartwig variants)
> - Searches for "Suzuki", "Heck", "amide coupling" by reaction_type return 0 results
> - The planner handles this: uses catalyst/reactant filters instead for those reaction types
> - This is an ORD dataset characteristic, not a system bug

> **Yield data has extreme outliers** (values up to 9×10¹⁹%)
> - Raw global average yield: ~92 trillion percent (meaningless)
> - `clean_statistics` (0-100% range): avg=63.83%, med=68.30% ← **use this**

> **Temperature data: 81% of records at or below 0°C** (likely default/unset values)
> - Raw global median: 0°C (meaningless)
> - `clean_statistics` (-100°C to 300°C): avg=13.63°C ← **use this**

> **Molecule registry is SMILES-only** — no compound names
> - Ethanol (CCO): 40,408. Acetone (CC(C)=O): 8,364. Benzene (c1ccccc1): 5,331.
> - Caffeine/aspirin not in registry. Planner falls back to `search_procedures` text search.

> **Catalyst identifiers are deeply fragmented**
> - Do not perform string-matching on the `name` field directly from DuckDB JSON arrays. A canonicalization mapping table is required.

## Architecture & Configuration

```
Dataset  →  DuckDB  →  Tools (10 tools)  →  FastAPI (15 endpoints including /chat, /providers)

Provider Layer (Dual-Routing)
  BaseProvider → OllamaProvider (live)
               → GroqProvider (live)
               → OpenAIProvider (stub)
               → AnthropicProvider (stub)
               → GeminiProvider (stub)
```

Recommended testing configuration:
```
Planner:   Ollama  /  qwen2.5:3b               (fast local intent detection)
Formatter: Groq    /  llama-3.3-70b-versatile  (fast cloud, high quality)
```

## Current Task (for next AI)

The architecture and planning for Phase 5 is fully complete. Begin executing the Phase 5 MVP defined in `experiment_comparison_design.md`.

1. **Catalyst Normalization Table**: Create a table/view in DuckDB (`ord.duckdb`) to collapse catalyst synonyms to a canonical identifier.
2. **File Upload FastAPI Endpoints**: Implement standard FastAPI file upload handling to ingest CSV and JSON payloads into the backend memory.
3. **Internal Schema Mapping**: Map uploaded payloads into the canonical JSON Experiment Schema.
4. **Metadata Similarity Matching (Option A)**: Write the SQL logic to query DuckDB for exact-match similarities over reactants and ±10°C temperature thresholds.
5. **Frontend Integration**: Introduce Dropzone components and updated Chat tooling in `ChatInterface.tsx`.

## Rules

- **Use DuckDB** for all data access currently. No Vector DBs or external graphs should be used for the MVP.
- **Preserve chemistry JSON structures**
- **Read `PROJECT_STRUCTURE.md`** before making any architectural or file modifications.
- **Update documentation** (`PROJECT_STATE.md`, `TASKS.md`, `AI_HANDOFF.md`, `CHANGE_LOG.md`) after major milestones.
- **Use `clean_statistics`** from yield/temperature when summarizing for users.
