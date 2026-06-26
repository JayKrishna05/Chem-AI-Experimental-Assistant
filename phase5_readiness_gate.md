# Phase 5 Readiness Gate

This document evaluates whether the current architecture is ready for Phase 5 (Experiment Upload & Comparison Engine).

## Architecture Review
Overall, the project structure is well-organized:
* **Planner (`backend/planner`)**: Very clean and deterministic. Isolates LLM logic from tool execution.
* **Tools (`backend/tools`)**: Clean separation between database querying and data processing.
* **FastAPI Routes (`backend/api`)**: Thin, stateless HTTP layer.
* **DuckDB Layer (`backend/database`)**: Schema is clear, and the read-only connection pool pattern is safe.
* **Documentation**: Detailed and up-to-date.

**Cleanup Opportunities (No Refactoring Done):**
* `top_yield_conditions` tool exists in `analytics_tools.py` but is not exposed in `api/routes.py`.
* Some JSON array casts (e.g., `CAST(catalysts_json AS VARCHAR)`) could be optimized in the future using DuckDB's JSON functions rather than string matching, but it works for now.

---

## Phase 5 Feature Readiness

### 1. File Uploads
* **Current State**: No POST routes exist in `api/routes.py` for handling uploads. The DuckDB schema (`schema.sql`) does not have tables for user experiments.
* **Status**: **Can Fix During Phase 5** (Building the upload routes and tables is the core work of Phase 5).

### 2. Experiment Parsing
* **Current State**: No parsing logic exists for custom user formats.
* **Status**: **Can Fix During Phase 5** (Adding new parser modules will not disrupt existing architecture).

### 3. Experiment Comparison
* **Current State**: The existing `compare_datasets` tool is fundamentally flawed because it ignores all chemical filters (like `reaction_type` or `source_dataset`). It only groups globally. If we try to build an "Experiment Comparison" engine on top of the current tools, we won't be able to filter by specific reaction types or conditions. 
* **Status**: **Must Fix Before Phase 5** (The foundational comparison tool needs to support filtering before we expand it to compare user uploads against the database).

### 4. Metadata Matching
* **Current State**: `schema.sql` lacks fields for user-defined metadata tags.
* **Status**: **Can Fix During Phase 5** (Adding a `user_metadata` column or table is straightforward and won't break existing read-only queries).
