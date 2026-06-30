# Tasks

## Phase 6: Frontend Integration & Upload Stabilization
- [x] Implement dropzone UI in chat interface.
- [x] Implement multipart upload frontend service.
- [x] Create `ComparisonResultCard` to visualize reports.
- [x] Fix provider failure cascading (`providerStatus` gracefully degrades).
- [x] **Upload Integration Audit**: Fix `useUpload.ts` toast lifecycle, integrate `tool_result_override` for Formatter bypass, improve yield classifications.

## Phase 6.5: Scientific Correctness & Data Access Layer
- [x] Extract DuckDB SQL from tools into Repositories (`ReactionRepository`, `ProcedureRepository`, `StatisticsRepository`).
- [x] Migrate `ComparisonService` to consume DAL instead of tools.
- [x] Enhance `ComparisonService` with hierarchical similarity search.
- [x] Add explicit assumptions and confidence scores to `EvidenceBundle`.
- [x] Establish Python benchmark suite for parsers and comparisons.

## Phase 7: PostgreSQL Migration
- [ ] Install PostgreSQL and configure Docker Compose.
- [ ] Migrate `ord.duckdb` schema to SQLAlchemy ORM models.
- [ ] Implement new SQL persistence logic in the Data Access Layer to support saving `CanonicalExperiment`s.
