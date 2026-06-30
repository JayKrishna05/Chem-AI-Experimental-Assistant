> **Historical Document**: This file was created during Phase 5 or 6 and is archived here for reference.

# Backend Code Quality Audit

## Overview
This audit evaluates the codebase following Phase 5 completion, prioritizing maintainability and structural cleanliness before shifting focus to UI and PostgreSQL capabilities.

## 🔴 Critical
*(No critical severity items found in the current backend snapshot. The codebase is remarkably clean of blocking technical debt.)*

## 🟠 High
### 1. Data Access Layer (DAL) vs Tool Coupling
- **Issue**: `backend/services/comparison_service.py` is deeply coupled to LLM tool functions in `backend/tools/analytics_tools.py`. The comparison service unwraps API-formatted dictionaries (`tool_version`, `contract_version`, `results`) to extract raw data.
- **Impact**: Any modification to the LLM tool schemas or formatting contracts will silently break backend business logic.
- **Effort**: Medium.
- **Action**: Extract DuckDB SQL queries from `backend/tools/` into `backend/database/repositories/`. Both the tools and the services should depend on the repositories.

### 2. Test Suite Fragmentation
- **Issue**: Core unit tests are arbitrarily split between `tests/` and `scripts/`. (`tests/test_experiment_upload.py` vs `scripts/test_planner.py`, `scripts/test_providers.py`, `scripts/test_tool_layer.py`).
- **Impact**: Inconsistent CI execution and discoverability. Running `pytest tests/` misses 80% of the test suite.
- **Effort**: Low.
- **Action**: Move all `test_*.py` files from `scripts/` into `tests/`.

## 🟡 Medium
### 3. CSV Parser Heuristics (`backend/experiment/parser.py`)
- **Issue**: Relies on standard `csv.DictReader` and simple string splits (`val.split(",")`). 
- **Impact**: Commas within IUPAC names (e.g., `1,2-dichloroethane`) will incorrectly split a single reactant into multiple entities. Duplicate column names overwrite rather than append.
- **Effort**: Medium.
- **Action**: Replace standard DictReader with a robust chemical tokenizer/CSV parser, or implement strict Pandas-based ingestion for uploads.

### 4. Catalyst Normalization Hardcoding (`backend/experiment/normalizer.py`)
- **Issue**: Uses an in-memory dictionary mapping for catalyst aliases (`"palladium" -> "Pd"`).
- **Impact**: Completely unscalable against the 11,000 fragmented synonym variants existing in the DuckDB database.
- **Effort**: Medium.
- **Action**: Move mapping logic to a `catalyst_normalization` SQL table inside DuckDB.

## 🟢 Low
### 5. Untyped Comparison Responses (`backend/services/comparison_service.py`)
- **Issue**: Returns an anonymous `dict[str, Any]` which `routes.py` passes directly to the frontend.
- **Impact**: Loss of IDE autocomplete and potential for silent KeyErrors.
- **Effort**: Low.
- **Action**: Implement the Pydantic `ComparisonResult` models designed in Phase 5.

### 6. File Sizes
- **Issue**: `backend/tools/analytics_tools.py` is nearing 30KB. It contains massive, multi-line SQL strings embedded directly in Python functions.
- **Impact**: Reduced readability.
- **Effort**: Low.
- **Action**: Move SQL strings to dedicated `.sql` files or a query-builder layer when migrating to PostgreSQL.
