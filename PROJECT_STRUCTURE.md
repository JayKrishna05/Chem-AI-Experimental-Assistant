# Project Structure Catalog

This is the authoritative codebase map for the AI Chemistry Engine V1. It serves as a guide for future developers, AI assistants, and onboarding workflows.

---

## 1. Subsystem Inventory

### Backend

#### `backend/main.py`
- **Purpose:** FastAPI entry point and application initialization.
- **Criticality:** HIGH
- **Dependencies:** FastAPI, `backend.chat.routes`
- **Used By:** `scripts/run_api.py`, Unicorn/Uvicorn
- **Notes:** Mounts the API routers and handles CORS.

#### `backend/chat/routes.py`
- **Purpose:** Defines the HTTP routes for the chat application, notably `/api/chat`.
- **Criticality:** HIGH
- **Dependencies:** `backend.chat.stream`
- **Used By:** `backend/main.py`
- **Notes:** Minimal logic; delegates directly to the SSE stream generator.

#### `backend/chat/stream.py`
- **Purpose:** Manages the Server-Sent Events (SSE) generator. Orchestrates the pipeline from user input to LLM Planner, executes the Tool, and routes the output to the Formatter.
- **Criticality:** HIGH
- **Dependencies:** `backend.planner.planner`, `backend.tools`, `backend.formatters.chemistry_formatter`
- **Used By:** `backend/chat/routes.py`
- **Notes:** The backbone of the orchestration layer.

#### `backend/planner/planner.py`
- **Purpose:** Invokes the LLM to decide which chemistry tool to execute.
- **Criticality:** HIGH
- **Dependencies:** `backend.providers`, `backend.planner.prompts`, `backend.planner.schema`
- **Used By:** `backend/chat/stream.py`
- **Notes:** Employs a brace-balancing algorithm to parse JSON out of raw LLM prose.

#### `backend/planner/schema.py`
- **Purpose:** Validates the tool filters chosen by the planner LLM against predefined Pydantic/Dictionary schemas. Also registers all `KNOWN_TOOLS`.
- **Criticality:** HIGH
- **Dependencies:** Built-in typing
- **Used By:** `backend/planner/planner.py`
- **Notes:** Schema changes must be duplicated here if tool function signatures change.

#### `backend/planner/prompts.py`
- **Purpose:** Contains the few-shot prompts and instructions for the LLM planner.
- **Criticality:** MEDIUM
- **Dependencies:** None
- **Used By:** `backend/planner/planner.py`
- **Notes:** Highly optimized for `qwen2.5:3b`. Be extremely careful expanding context size.

#### `backend/providers/base.py`
- **Purpose:** Abstract Base Class defining the LLM Provider interface.
- **Criticality:** MEDIUM
- **Dependencies:** ABC
- **Used By:** Provider implementations, `backend/planner/planner.py`
- **Notes:** Enforces the `generate()` method signature.

#### `backend/providers/provider_factory.py`
- **Purpose:** Instantiates the correct provider (Ollama or Groq) based on runtime flags.
- **Criticality:** HIGH
- **Dependencies:** `ollama_provider`, `groq_provider`
- **Used By:** `backend/planner/planner.py`, Formatter
- **Notes:** Abstracts provider complexity from the execution logic.

#### `backend/providers/ollama_provider.py`
- **Purpose:** Interface to local Ollama models.
- **Criticality:** HIGH
- **Dependencies:** `httpx`
- **Used By:** `provider_factory.py`
- **Notes:** Subject to local hardware timeouts. Configured to handle API failures gracefully.

#### `backend/providers/groq_provider.py`
- **Purpose:** Interface to the remote Groq cloud API.
- **Criticality:** HIGH
- **Dependencies:** `httpx`
- **Used By:** `provider_factory.py`
- **Notes:** Requires `ORD_GROQ_API_KEY`. Extremely fast, used for formatter logic.

#### `backend/tools/analytics_tools.py`
- **Purpose:** Executes SQL queries against DuckDB for statistical and comparative chemistry.
- **Criticality:** HIGH
- **Dependencies:** `duckdb`
- **Used By:** `backend/planner/planner.py`
- **Notes:** Houses the core Phase 4 tools (`compare_datasets`, `yield_statistics`, etc).

#### `backend/tools/chemistry_tools.py`
- **Purpose:** Executes basic lookups for SMILES, reactions, and procedures.
- **Criticality:** HIGH
- **Dependencies:** `duckdb`
- **Used By:** `backend/planner/planner.py`
- **Notes:** Handles structural subset queries.

### Frontend

#### `frontend/src/app/page.tsx`
- **Purpose:** The root Next.js Server/Client component wrapping the UI.
- **Criticality:** HIGH
- **Dependencies:** `ChatInterface.tsx`
- **Used By:** Next.js Router
- **Notes:** Entry point for the React tree.

#### `frontend/src/components/ChatInterface.tsx`
- **Purpose:** Main conversational layout. Hosts the message list and input bar.
- **Criticality:** HIGH
- **Dependencies:** `useChatStream.ts`, `useModels.ts`, `ChatMessage.tsx`
- **Used By:** `page.tsx`
- **Notes:** Contains the Provider dropdown selections.

#### `frontend/src/components/ChatStream.tsx` / `useChatStream.ts`
- **Purpose:** Handles the actual SSE connection and parses the streaming chunks from the backend.
- **Criticality:** HIGH
- **Dependencies:** Browser `fetch` / EventStream APIs
- **Used By:** `ChatInterface.tsx`
- **Notes:** Extremely brittle SSE parsing logic; do not modify without extensive testing.

#### `frontend/src/hooks/useModels.ts`
- **Purpose:** Fetches available models from Ollama/Groq to populate UI dropdowns.
- **Criticality:** MEDIUM
- **Dependencies:** FastAPI `/api/models`
- **Used By:** `ChatInterface.tsx`
- **Notes:** Falls back gracefully if Ollama is offline.

### Scripts & Tests

#### `scripts/test_planner_benchmark.py`
- **Purpose:** The authoritative automated test harness for LLM Planner routing.
- **Criticality:** HIGH
- **Dependencies:** `backend.planner`, `tests/planner_benchmark_cases.json`
- **Used By:** CI / Developer Workflows
- **Notes:** MUST be run to validate any prompt or schema changes.

#### `tests/planner_benchmark_cases.json`
- **Purpose:** 100 benchmark queries with their expected tools and filters.
- **Criticality:** HIGH
- **Dependencies:** None
- **Used By:** `test_planner_benchmark.py`
- **Notes:** Living document. Add edge-cases here.

#### `scripts/audit_catalysts.py`
- **Purpose:** Normalization analysis script for DuckDB catalyst variants.
- **Criticality:** LOW
- **Dependencies:** `duckdb`
- **Used By:** Architecture planning
- **Notes:** Run periodically to track data cleanliness.

---

## 2. Special Sections

### Core Request Pipeline
1. **User** types a message in `frontend/src/components/ChatInput.tsx`.
2. **Frontend** `useChatStream.ts` opens a POST request to `/api/chat`.
3. **FastAPI** `backend/chat/routes.py` receives the request and delegates to `backend/chat/stream.py`.
4. **Stream** invokes `backend/planner/planner.py` (The Planner).
5. **Planner** uses `backend/providers/provider_factory.py` to call the LLM and get a JSON decision.
6. **Planner** validates the JSON via `backend/planner/schema.py`.
7. **Stream** routes the validated JSON to the appropriate function in `backend/tools/`.
8. **Tool** queries DuckDB and returns raw JSON results.
9. **Stream** sends the raw JSON to the Frontend (yielding a Tool Result block).
10. **Stream** passes the Tool JSON to `backend/formatters/chemistry_formatter.py`.
11. **Formatter** streams Markdown back via `provider_factory.py`.
12. **Frontend** renders the Markdown.

### Planner System
The Planner (`planner.py`) is essentially a robust prompt engineer wrapped around the LLM (`prompts.py`). It enforces rigid JSON output and falls back through retry loops if the LLM hallucinates markdown or prose. Once JSON is acquired, it rigorously checks parameter validity against `schema.py`.

### Provider System
The Provider architecture abstracts local constraints. `base.py` guarantees both `OllamaProvider` and `GroqProvider` offer `.generate()` and `.stream()`. The `provider_factory.py` is dynamically controlled by the Frontend UI dropdowns, allowing mixed routing (e.g., Planner runs locally on Qwen, Formatter runs fast on Groq).

### Benchmarking System
Driven by `test_planner_benchmark.py` and `planner_benchmark_cases.json`. It completely bypasses the FastAPI and Tool layers to directly evaluate the LLM Planner's ability to map English text to JSON tool/filter pairs. Accuracy improvements are the primary metric for project success.

### Analytics Tool Layer
All tools reside in `backend/tools/analytics_tools.py` and query DuckDB:
- `dataset_summary`: Total counts only. Filters: none.
- `catalyst_statistics`: Most common catalysts. Filters: reaction_type, source_dataset, limit.
- `reagent_statistics`: Most common solvents/reagents. Filters: reaction_type, source_dataset, limit.
- `yield_statistics`: Yield % stats. Filters: reaction_type, source_dataset.
- `temperature_statistics`: Temperature stats. Filters: reaction_type, source_dataset.
- `source_dataset_statistics`: Dataset coverage ranking. Filters: reaction_type, sort_by, limit.
- `reaction_type_statistics`: Reaction type ranking. Filters: source_dataset, sort_by, limit.
- `compare_datasets`: Compare side-by-side datasets or reaction_types. Filters: group_by.
- `top_yield_conditions`: Find the conditions that yield the highest %. Filters: reaction_type.
- `dataset_quality_report`: Show nullability and metadata completeness. Filters: none.

### Documentation Map
- **`PROJECT_STATE.md`**: The current snapshot. Defines what phase we are in and overarching goals.
- **`PROJECT_STRUCTURE.md`**: (This file) The codebase map. Update when adding new files or massive pipeline changes.
- **`CHANGE_LOG.md`**: Running timeline of accomplished milestones.
- **`TASKS.md`**: Granular execution checklists for the current active phase.
- **`AI_HANDOFF.md`**: Context retention specifically curated for LLM Agents starting new sessions.

---

## 3. Refactor Candidates

### `backend/tools/analytics_tools.py`
- **Issue:** Approaching 600+ lines. Contains massive multi-line SQL strings intermingled with Python logic.
- **Recommendation:** Extract SQL strings into a dedicated `backend/sql/` directory as `.sql` files, or use an ORM / query builder if complexity increases.

### `backend/chat/stream.py`
- **Issue:** Handles SSE serialization, Planner invocation, Tool Dispatch, *and* Formatter invocation. It is violating the Single Responsibility Principle.
- **Recommendation:** Decouple into an `Orchestrator` class that handles the domain logic, leaving `stream.py` to handle only the HTTP SSE protocol wrapping.

### `frontend/src/hooks/useChatStream.ts`
- **Issue:** Extremely fragile buffer parsing for the custom `[TOOL]` vs text SSE payloads. 
- **Recommendation:** Move to a more robust library like `@microsoft/fetch-event-source` and standardize the payload envelopes to rigid JSON.
