# Technical Debt Review

This document audits the Phase 5 implementation (Experiment Upload & Comparison Engine) for technical debt, duplicated logic, and structural shortcomings before scaling.

## High Impact / High Priority

### 1. Data Access Layer (DAL) Absence
- **Issue**: `comparison_service.py` is directly coupled to `backend/tools/analytics_tools.py` and `chemistry_tools.py`. The tool layer returns UI-formatted JSON with `count` and `contract_version` fields, which the service awkwardly unpacks.
- **Impact**: Any change to the LLM tool contracts breaks backend business logic.
- **Effort**: Medium.
- **Resolution**: Extract all DuckDB SQL queries from `analytics_tools.py` into a new `backend/database/repositories/` layer. Both the tools and the comparison service should call the repository layer, which returns pure Python models.

### 2. Normalization Dictionary Hardcoding
- **Issue**: `backend/experiment/normalizer.py` relies on an in-memory dictionary for catalyst aliases (`cat_aliases = {"palladium": "Pd", ...}`).
- **Impact**: Inadequate for the 11,000 fragmented catalyst names in the DB.
- **Effort**: Medium.
- **Resolution**: This must become data-driven. Implement the planned `catalyst_normalization` table in DuckDB and have the normalizer query it.

## Medium Impact / Medium Priority

### 3. Parser CSV Heuristics
- **Issue**: `parse_csv` uses `csv.DictReader` and simple `val.split(",")` for array fields.
- **Impact**: Duplicate headers overwrite each other instead of appending. Commas inside chemical names (e.g., `1,2-dichloroethane`) will incorrectly split a single reactant into two.
- **Effort**: Medium.
- **Resolution**: Implement a robust `pandas` or strict regex tokenizer for chemical CSV parsing, replacing standard `csv.DictReader`.

### 4. Untyped Comparison Responses
- **Issue**: `compare_experiment` returns a `dict[str, Any]` containing nested comparisons.
- **Impact**: Loss of IDE autocomplete, hard to document in OpenAPI, and prone to silent `KeyError`s.
- **Effort**: Low.
- **Resolution**: Implement the typed `ComparisonResult` Pydantic models proposed in `comparison_result_design.md`.

## Low Impact / Deferred

### 5. Text Parser Regex Simplicity
- **Issue**: `parse_text` relies on extremely basic regex (e.g., `\d+ %`) to find yield and temperature.
- **Impact**: Susceptible to false positives (e.g., "5% catalyst loading" -> `yield_percent=5.0`).
- **Effort**: High (requires moving to NLP/LLM).
- **Resolution**: Await the implementation of the LLM-assisted PDF parsing pipeline, which will organically replace deterministic regex with semantic extraction.

### 6. Missing Persistence
- **Issue**: Uploaded experiments are stored in memory and lost after the request completes.
- **Impact**: Users cannot build historical libraries of their experiments.
- **Effort**: High.
- **Resolution**: Implement `backend/experiment/storage.py` and migrate the operational DB to PostgreSQL as outlined in `experiment_persistence_plan.md`.
