# Dependency Review

## Current Environment
The project currently relies on an extremely lean `requirements.txt`:
```
duckdb==1.5.3
fastapi==0.137.1
uvicorn==0.49.0
pydantic==2.11.7
httpx==0.28.1
```

## Observations & Analysis

1. **Hyper-Optimized Footprint**: 
   - The backend avoids heavy ORMs (like SQLAlchemy) and massive data science libraries (Pandas/NumPy), keeping the Docker image and virtual environment extremely small.
   - External API calls are handled via `httpx` and `urllib`, eliminating the need for bulky vendor SDKs (e.g., `openai`, `groq` packages).

2. **Duplicate Functionality**:
   - `httpx` is used for testing and remote API calls, but standard library `urllib` is occasionally used in provider implementations to avoid async overhead. This is acceptable for now but could be consolidated to pure `httpx` (using `httpx.Client()`).

3. **Missing (but Required) Packages**:
   - **Testing**: `pytest` is not explicitly listed in `requirements.txt`. Tests are currently run natively via `python scripts/test_x.py`. If CI/CD is introduced, `pytest` should be added as a dev dependency.
   - **Multipart Uploads**: FastAPI requires `python-multipart` to accept raw file uploads. As we transition Phase 5 to support drag-and-drop file binaries instead of pasted string payloads, `python-multipart` must be added.

4. **Future Dependencies (Optional/Deferred)**:
   - `pandas`: May become necessary for robust CSV chemical parsing if `csv.DictReader` limitations (e.g., duplicate columns) prove too complex to write manual heuristics for.
   - `sqlalchemy` + `psycopg2-binary`: Required only when the operational database fully migrates from DuckDB to PostgreSQL.

## Recommendations
- **Add**: `python-multipart` (required for `/experiments/upload` endpoint binary ingestion).
- **Add (Dev)**: `pytest` and `pytest-asyncio` to standardize the test execution suite.
- **Maintain**: Continue avoiding heavy vendor SDKs (OpenAI, Anthropic) in favor of lightweight `httpx` REST calls to maintain the minimal install size.
