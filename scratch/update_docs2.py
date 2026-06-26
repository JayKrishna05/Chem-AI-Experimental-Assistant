
import re

# Update CHANGE_LOG.md
with open("CHANGE_LOG.md", "r", encoding="utf-8") as f:
    text = f.read()

new_log = """
### 2026-06-26
- **Test Suite Consolidation**: Unified all tests under pytest, moved `scripts/test_*.py` to `tests/`.
- **Multipart Upload API**: Transitioned experiment upload endpoints to native FastAPI `UploadFile`.
- **Parser Architecture Refactoring**: Split monolithic `parser.py` into a package (`parser/dispatcher.py`, `parser_csv.py`, `parser_json.py`, `parser_xlsx.py`, `parser_text.py`) and added `UploadMetadata` tracking.
- **ADR Generation**: Captured major architectural decisions in `adr/`.

"""
text = text.replace("## Timeline", "## Timeline\n" + new_log)
with open("CHANGE_LOG.md", "w", encoding="utf-8") as f:
    f.write(text)

# Update PROJECT_STATE.md
with open("PROJECT_STATE.md", "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace("The backend is currently in a stable \"feature-complete MVP\" state", "The backend is currently in a stable \"frozen MVP\" state after the final Consolidation Sprint")
with open("PROJECT_STATE.md", "w", encoding="utf-8") as f:
    f.write(text)

# Update PROJECT_STRUCTURE.md
with open("PROJECT_STRUCTURE.md", "r", encoding="utf-8") as f:
    text = f.read()

parser_replacement = """#### `backend/experiment/parser/`
- **Purpose:** A modular package that dynamically dispatches and parses uploaded files (JSON, CSV, XLSX, Text) into `CanonicalExperiment` instances using dedicated sub-modules.
- **Criticality:** MEDIUM
- **Dependencies:** `openpyxl`, `backend.experiment.models`
- **Used By:** `backend/api/routes.py`
- **Notes:** Extensible dispatch architecture. Includes `dispatcher.py`, `parser_csv.py`, `parser_json.py`, `parser_xlsx.py`, `parser_text.py`."""

text = re.sub(r"#### `backend/experiment/parser\.py`.*?Notes:.*?\n", parser_replacement + "\n\n", text, flags=re.DOTALL)
with open("PROJECT_STRUCTURE.md", "w", encoding="utf-8") as f:
    f.write(text)

# Update AI_HANDOFF.md
with open("AI_HANDOFF.md", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("Next critical architectural shift: **Data Access Layer (DAL)** extraction.", "Recent consolidation unified tests under pytest and established a multipart file upload pipeline via an extensible parser dispatcher. Next phase focuses on User-Facing UI and Postgres migration.")
with open("AI_HANDOFF.md", "w", encoding="utf-8") as f:
    f.write(text)

# Update TASKS.md
with open("TASKS.md", "w", encoding="utf-8") as f:
    f.write("""# Tasks

## Phase 6: User-Facing Functionality and UI Integration
- [ ] Build Upload UI (Dropzone integration)
- [ ] Experiment Persistence (Database schema for uploaded experiments)
- [ ] PostgreSQL Migration
- [ ] Semantic Search / Embeddings
""")

