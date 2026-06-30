# Technical Debt Review (Current)

## Overview
This is an updated technical debt audit focusing only on genuine, high-impact structural issues that inhibit scaling and correctness.

### Critical Priority

#### 1. Lack of a Data Access Layer (DAL)
*   **Issue**: SQL query strings and DuckDB connections are tightly bound within `backend/tools/analytics_tools.py`. The `ComparisonService` relies on these tool functions, forcing it to parse UI-oriented JSON contracts rather than pure data.
*   **Why it matters**: It violates the Single Responsibility Principle. A change to a chat tool's JSON output format will silently break the backend comparison logic.
*   **Action**: Extract DuckDB queries into a `backend/database/repositories/` layer that returns pure Pydantic models or standard Python objects. Both the chat tools and the `ComparisonService` should consume this layer.

#### 2. The 99.97% NULL `reaction_type` Problem
*   **Issue**: Crucial functions like `top_yield_conditions` require a `reaction_type` to group by, essentially ignoring 99.97% of the dataset.
*   **Why it matters**: Results are statistically meaningless if they discard the vast majority of the source truth.
*   **Action**: SQL tools must be updated to fallback to structural matching (reactants + products + catalysts) when grouping or filtering, rather than strictly requiring `reaction_type`.

### High Priority

#### 3. Catalyst Normalization Hardcoding
*   **Issue**: `backend/experiment/normalizer.py` relies on an in-memory dictionary.
*   **Why it matters**: There are over 11,000 fragmented catalyst names (e.g., "Pd/C", "palladium on carbon"). An in-memory dict cannot scale to this complexity without becoming unmaintainable.
*   **Action**: Build the `catalyst_normalization` lookup table inside DuckDB.

#### 4. Untyped Comparison Responses
*   **Issue**: `compare_experiment` returns a deeply nested, untyped `dict[str, Any]`.
*   **Why it matters**: It prevents IDE safety, breaks OpenAPI schema generation, and obscures the provenance (EvidenceBundle) of where comparisons were sourced.
*   **Action**: Implement `ComparisonResult` and `EvidenceBundle` as strict Pydantic models.

### Medium Priority

#### 5. CSV Parsing Instability
*   **Issue**: `parse_csv` uses a naive string split on commas for array fields.
*   **Why it matters**: IUPAC names frequently contain commas (e.g., `1,2-dichloroethane`), which causes the parser to split a single molecule into multiple invalid fragments.
*   **Action**: Implement a robust tokenizer for the CSV parser that respects quoted strings, or migrate strictly to JSON/XLSX for complex chemical lists.

#### 6. Orchestration Coupling in `stream.py`
*   **Issue**: `backend/chat/stream.py` mixes SSE HTTP protocol logic with Planner invocation and Provider generation.
*   **Why it matters**: Hard to unit test the orchestration logic without mocking HTTP streams.
*   **Action**: Decouple into an `Orchestrator` domain class.
