# Test Coverage Review

## Overview
The AI Chemistry Engine V1 features an extensive but architecturally fragmented test suite. While functional coverage of the LLM Planner and API endpoints is high, unit tests for underlying modules are sparser.

## Coverage Breakdown

### 1. High Coverage Areas
- **LLM Planner Routing**: `scripts/test_planner_benchmark.py` and `tests/planner_benchmark_cases.json` rigorously test 100 benchmark queries against the actual LLM integration.
- **Provider Abstraction**: `scripts/test_providers.py` ensures Ollama and Groq APIs adhere to strict timeout and fallback contracts.
- **API Endpoints**: `scripts/test_api_endpoints.py`, `scripts/test_analytics_endpoints.py`, and `tests/test_experiment_endpoints.py` provide excellent smoke testing for all FastAPI routes, capturing regressions in response contracts.
- **Phase 5 Upload Pipeline**: `tests/test_experiment_upload.py` thoroughly tests the decoupled parsing, normalization, and validation logic, including stress tests for noisy CSVs.

### 2. Weak Coverage Areas
- **Chemistry Tools (`backend/tools/chemistry_tools.py`)**: There are virtually no isolated unit tests verifying the DuckDB SQL extraction logic for `search_reactions`, `molecule_lookup`, or `search_procedures`. Testing relies entirely on the API endpoint smoke tests.
- **Formatter Resilience**: While A/B evaluation scripts exist (`scripts/run_formatter_ab.py`), there are no continuous automated unit tests verifying the Formatter's markdown streaming chunk logic (`backend/chat/formatter.py`).

### 3. Missing Edge Cases
- **Comparison Engine Gaps**: `tests/test_experiment_endpoints.py` tests that the comparison engine returns a 200 OK, but lacks assertions verifying mathematical accuracy (e.g., if a user uploads a yield of 85%, does `is_suboptimal` correctly trigger when the DB average is 95%?).
- **Upload Pipeline Gaps**: The CSV parser tests do not currently simulate quotes escaping commas (e.g., `"1,2-dichloroethane",Pd`), which is a known blindspot for standard `split(",")`.

## Architectural Inconsistencies
- **Fragmented Directories**: 80% of the test suite lives in `scripts/` (e.g., `test_planner.py`), while 20% lives in `tests/`. This makes CI execution and coverage reporting extremely difficult.

## Recommendations
1. Move all `scripts/test_*.py` files into the `tests/` directory.
2. Introduce a `pytest` configuration to run the entire suite automatically.
3. Write isolated unit tests for `chemistry_tools.py` focusing on complex SQL filter constructions (especially exact vs substring matching for molecules).
