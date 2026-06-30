> **Historical Document**: This file was created during Phase 5 and is archived here for reference.

# Phase 5 Architecture Review

## Overview
Phase 5 successfully introduced an independent Experiment Upload & Comparison Pipeline. The architecture introduces four distinct stages:
1. **Parser**: Translates raw JSON, CSV, Text into a `CanonicalExperiment`.
2. **Normalizer**: Standardizes units, field aliases, and string casing.
3. **Validator**: Inspects bounds and missing fields, emitting warnings via `ValidationResult`.
4. **Comparison Service**: Uses existing DuckDB tools to check the validated experiment against the database.

## Architectural Inconsistencies & Coupling

### 1. The `ComparisonService` is Tightly Coupled to `analytics_tools.py`
Currently, `backend/services/comparison_service.py` directly imports and calls `search_reactions`, `top_yield_conditions`, and `temperature_statistics`. 
- **The Problem:** The tool layer (`analytics_tools.py` and `chemistry_tools.py`) is designed as a rigid API layer for the LLM Planner. It enforces strict Pydantic schemas and standard response contracts (e.g., `count`, `returned_rows`, `contract_version`). The comparison service currently extracts data out of these UI-facing tool contracts.
- **The Solution:** A true Data Access Layer (DAL) / Repository pattern. The core SQL querying logic should be extracted from `analytics_tools.py` into `backend/database/repositories/`. Both the LLM tools and the Comparison Service would then consume the shared Repository layer, exchanging pure Python models instead of JSON-formatted tool responses.

### 2. Normalization Hardcoding
The `normalizer.py` currently hardcodes the catalyst mapping (`palladium` -> `Pd`). 
- **The Problem:** This works for MVP but will not scale given the 11,000 fragmented synonyms identified in the DuckDB database.
- **The Solution:** The Normalizer must eventually query the `catalyst_normalization` table (to be implemented in DuckDB) rather than relying on in-memory dictionaries.

## Future Migration Path (No Action Required Yet)

When we move to PostgreSQL / SQLAlchemy in the future:
1. Create `backend/database/repository.py` holding raw data fetchers.
2. Refactor `backend/tools/` to solely handle LLM schema validation and response formatting.
3. Refactor `backend/services/` to execute complex business logic (like comparison) by composing multiple repository calls.
