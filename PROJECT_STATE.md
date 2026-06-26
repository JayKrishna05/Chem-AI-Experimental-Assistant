# PROJECT STATE

Last Updated: 2026-06-26

## Current Phase

- [x] Phase 5: Experiment Upload & Comparison Engine (Backend MVP)
- [x] Phase 6: User-Facing Functionality and UI Integration
- [ ] Phase 7: Local DuckDB to PostgreSQL Migration (Scale-Up)
- [ ] Phase 8: Semantic Search / Embeddings

## Completed

- ORD dataset converted to JSONL
- Procedure database extracted
- Molecule registry built
- DuckDB schema created and ingested (`backend/database/ord.duckdb`)
- DuckDB-backed tool layer and Analytics Tools implemented
- FastAPI backend layer and SSE chat stream implemented
- Next.js 15 Frontend Chat Interface with TailwindCSS and shadcn/ui
- **Model Management & Dual-Provider Architecture**: Implemented full `OllamaProvider` and `GroqProvider` routing.
- **Planner System Refined**: Planner prompt and schema updated to support 10 active tools. Final Benchmark Accuracy: 59.0%.
- **Architecture Cleanup**: Unified filtering schemas, standardizing the DuckDB SQL tooling into `backend/tools/filters.py`.
- **Phase 5 MVP**: Created the Experiment Upload pipeline featuring decoupled Parsing, Normalization, Validation, and Comparison Service modules. New endpoints `POST /experiments/parse` and `POST /experiments/compare` are live.
- **Phase 6 Completed**: Integrated dropzone UI, multipart upload service, `ComparisonResultCard`, and Formatter pipeline bypass for direct upload summarization. Fixed provider resiliency gracefully degrading when unavailable.

## Critical Database Facts

- **99.97% of reactions (2,375,370 / 2,376,120) have `reaction_type = NULL`**
- **Yield data contains extreme outliers** (handled via `clean_statistics`).
- **Temperature data: 81% of records at or below 0°C** (likely default values).
- **Molecule registry contains SMILES only** — no compound names.
- **Catalyst identifiers are highly fragmented**: Over 11,000 catalyst entities missing SMILES entirely; names like "Pd/C" span dozens of distinct string representations.

Datasets:
- Reactions: 2,376,120
- Procedures: 1,788,170
- Molecules: 1,993,180
- Source Datasets: 542

## Current Focus

- **Catalyst Normalization Engine**: We still need to build the `catalyst_normalization` lookup table in DuckDB to handle the 11,000 fragmented synonym hashes.
- **Architecture Readiness**: Preparing for Phase 7 (PostgreSQL Migration) since the React frontend and Backend pipeline are now stable.

## Next Milestones

1. **Data Access Layer (DAL) Refactor**: Extract DuckDB SQL strings from `analytics_tools.py` into a true Repository layer so the Comparison Service can consume them natively without parsing UI tool contracts.
2. **Frontend Integration**: Add file dropzone UI to the chat interface.
3. **Catalyst Normalization**: Create the canonical mapping table in DuckDB to replace the hardcoded `normalizer.py` dictionary.
4. **Strong Typing & Provenance**: Upgrade `ComparisonService` to return `ComparisonResult` models equipped with `EvidenceBundle` provenance tracking.
5. **Database Migration**: Plan the transition from DuckDB to PostgreSQL/SQLAlchemy.

## Infrastructure Status

- **Database**: DuckDB fully populated.
- **Backend**: FastAPI retrieval, dual-provider routing, and experiment upload live.
- **Planner**: 59.0% accuracy. 10 tools active.
- **Frontend**: Responsive chat UI with provider selectors.

## Documentation Map
- **`PROJECT_STATE.md`**: This document (high level status).
- **`PROJECT_STRUCTURE.md`**: The authoritative codebase map and architectural catalog.
- **`CHANGE_LOG.md`**: Running timeline of accomplished milestones.
- **`TASKS.md`**: Granular execution checklists for the current active phase.
- **`AI_HANDOFF.md`**: Context retention specifically curated for LLM Agents starting new sessions.
- **`architecture_diagrams.md`**: Visual Mermaid diagrams of the system architecture.

## Repository Status

- Git is initialized for this workspace
- GitHub remote `origin` exists
- Repository: https://github.com/JayKrishna05/Chem-AI-Experimental-Assistant
- Milestone commits and pushes to `origin/main` are expected
- Force pushes and history rewrites are not allowed
