# Tasks

## Phase 6: Frontend Integration & Upload Stabilization
- [x] Implement dropzone UI in chat interface.
- [x] Implement multipart upload frontend service.
- [x] Create `ComparisonResultCard` to visualize reports.
- [x] Fix provider failure cascading (`providerStatus` gracefully degrades).
- [x] **Upload Integration Audit**: Fix `useUpload.ts` toast lifecycle, integrate `tool_result_override` for Formatter bypass, improve yield classifications.

## Phase 7: PostgreSQL Migration
- [ ] Install PostgreSQL and configure Docker Compose.
- [ ] Migrate `ord.duckdb` schema to SQLAlchemy ORM models.
- [ ] Move DuckDB SQL strings out of `analytics_tools.py` into a Data Access Layer (DAL).
- [ ] Migrate tool layer to consume DAL instead of DuckDB directly.
