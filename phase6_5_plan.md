# Phase 6.5 Implementation Plan

## Objective
This sprint bridges the gap between the completed Phase 6 UI and the upcoming Phase 7 PostgreSQL migration. We will NOT implement PostgreSQL persistence yet. The strict focus is on rectifying scientific correctness, solidifying the Data Access Layer, and enhancing provenance.

## Recommended Implementation Order

### Step 1: Data Access Layer (DAL) Refactor
*   **Goal**: Decouple database logic from the chat tools.
*   **Implementation**: Create `backend/database/repositories/reaction_repo.py` and `procedure_repo.py`. Migrate the raw DuckDB SQL strings from `analytics_tools.py` into these repositories. Ensure repositories return generic Python data structures. 
*   **Reasoning**: This must happen first so that subsequent changes to the Comparison Service can consume clean API contracts rather than UI tool outputs.

### Step 2: Fix Similarity Search & Scientific Correctness
*   **Goal**: Stop using `reactants[0]` heuristics and fix the 99.97% NULL `reaction_type` flaw.
*   **Implementation**:
    *   Update repository queries to allow exact or subset matching of multiple reactants/products simultaneously.
    *   Rewrite `top_yield_conditions` to group by `(reactants, products)` if `reaction_type` is NULL.
    *   Update temperature anomaly logic to exclude 0°C defaults from the baseline average.
*   **Reasoning**: Resolves the most critical scientific integrity bugs identified in the audit.

### Step 3: Strong Typing & Evidence/Provenance
*   **Goal**: Formalize the outputs of the Comparison Service.
*   **Implementation**: Create `EvidenceBundle` and `ComparisonResult` Pydantic models in `backend/experiment/models.py`. Ensure every comparison claim (e.g., yield anomaly) attaches the specific ORD `reaction_id`s that justify the claim. Update `comparison_service.py` to return this model.
*   **Reasoning**: Users need to trace AI claims back to the source literature. Typed models ensure the frontend can predictably render citations.

### Step 4: Catalyst Normalization Engine
*   **Goal**: Replace the hardcoded dictionary in `normalizer.py`.
*   **Implementation**: Execute a migration script to create a `catalyst_normalization` table in `ord.duckdb`. Update `normalizer.py` to query this table for resolving fragmented strings ("Pd/C") to canonical SMILES.
*   **Reasoning**: Solves a major data cleanliness issue before we migrate data to PostgreSQL.

### Step 5: Parser Improvements & CSV Fixes
*   **Goal**: Fix parsing of IUPAC names containing commas.
*   **Implementation**: Update `parser_csv.py` to utilize standard CSV quoted-string rules or strict regex tokenization. Add edge-case tests.
*   **Reasoning**: A small but high-impact fix for data ingestion reliability.

### Step 6: Frontend & Documentation Polish
*   **Goal**: Present the new Evidence bundles in the UI.
*   **Implementation**: Update `ComparisonResultCard.tsx` to display clickable `reaction_id` citations next to claims. Ensure all outdated documentation is correctly archived.
*   **Reasoning**: Completes the feedback loop, presenting the newly accurate, provenanced data to the end user.
