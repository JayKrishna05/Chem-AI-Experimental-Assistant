> **Historical Document**: This file was created during Phase 5 or 6 and is archived here for reference.

# Refactor Backlog

This backlog contains only high-value, strictly necessary architectural improvements to stabilize the backend before major feature scaling (like PostgreSQL migration and UI integration). Speculative refactors are excluded.

---

### 1. Data Access Layer (DAL) Implementation
- **Description**: Move DuckDB SQL strings out of `backend/tools/` into a `backend/database/repositories/` layer. Both LLM tools and the Comparison Service should consume this layer.
- **Benefit**: Decouples business logic from UI/LLM contracts. Eradicates the brittle unpacking of `tool_version` dicts inside the comparison service.
- **Estimated Effort**: High (requires rewriting all tool functions to use the repo layer).
- **Blocks Future Work?**: **YES**. Without this, migrating to PostgreSQL/SQLAlchemy later will require rewriting both the Tool layer AND the Comparison layer simultaneously.

### 2. Catalyst Normalization Table
- **Description**: Replace the hardcoded `{"palladium": "Pd"}` dictionary in `normalizer.py` with a DuckDB `catalyst_normalization` lookup table query.
- **Benefit**: Ensures comparison similarity matching actually works across the 11,000 distinct catalyst name fragments in the database.
- **Estimated Effort**: Medium (requires SQL table creation and data cleaning).
- **Blocks Future Work?**: **YES**. If omitted, the `top_yield_conditions` and `similar_reactions` tools will confidently return `0 results` for uploaded user experiments due to string mismatch.

### 3. Test Suite Consolidation
- **Description**: Move all `test_*.py` files currently sitting in `scripts/` into the `tests/` directory and configure `pytest`.
- **Benefit**: Enables unified `pytest` execution, ensuring regressions are caught automatically across the entire project in one command.
- **Estimated Effort**: Low.
- **Blocks Future Work?**: No, but highly recommended before adding more complex integration tests for the UI.

### 4. Typed Comparison Results & Provenance
- **Description**: Update `ComparisonService` to return Pydantic `ComparisonResult` models equipped with `EvidenceBundle` objects containing raw database samples.
- **Benefit**: Provides strict type safety for the Next.js frontend to consume, and eliminates black-box hallucination risks by passing exact SQL evidence to the LLM Formatter.
- **Estimated Effort**: Low.
- **Blocks Future Work?**: No, but vastly improves the user trust in the AI's analytical conclusions.

### 5. Multi-part Upload API Modification
- **Description**: Update `POST /experiments/upload` (or `parse`/`compare`) to accept `UploadFile` (multipart/form-data) instead of JSON string bodies containing `content: "csv text..."`.
- **Benefit**: Enables the frontend UI Dropzone component to stream file binaries natively.
- **Estimated Effort**: Low (FastAPI makes this trivial).
- **Blocks Future Work?**: **YES**. Blocks the Next.js frontend integration.
