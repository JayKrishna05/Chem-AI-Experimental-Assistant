# AI HANDOFF

Date: 2026-06-16

## Current Status

Phase 3 Backend completed. `POST /chat` with SSE streaming is finished.

Implemented this milestone:

- `backend/api/models.py` — Added `ChatRequest` model.
- `backend/chat/formatter.py` — `format_response` function that takes `PlannerResult` and queries the LLM for a natural-language summary of the raw tool JSON.
- `backend/chat/stream.py` — `stream_chat_events` generator. Emits SSE sequence: `thinking` -> `tool_selected` -> `tool_result` (with both raw data & formatted text) -> `done`.
- `backend/api/chat_routes.py` — FastAPI router with the `/chat` endpoint.
- `scripts/test_chat_endpoint.py` — E2E endpoint smoke tests using a mocked Provider and FastAPI `TestClient`.

All prior work remains intact. Backend is now 100% database-agnostic at the chat and planner layer, allowing smooth transition to PostgreSQL + pgvector later.

## Architecture (Current)

```
Dataset  →  DuckDB  →  Tools  →  FastAPI (11 endpoints including /chat)

Provider Layer
  BaseProvider → OllamaProvider (live) / stubs

Planner Layer
  User question → Planner.plan(question) → JSON extraction → Tool dispatch → PlannerResult

Chat Layer (NEW)
  POST /chat (SSE Stream)
    ↓
  emit: {type: "thinking"}
    ↓
  run: Planner.plan()
    ↓
  emit: {type: "tool_selected", tool: "...", filters: {...}}
    ↓
  run: format_response() (LLM summary call)
    ↓
  emit: {type: "tool_result", result: {...raw...}, text: "...summary..."}
    ↓
  emit: {type: "done"}
```

## SSE Event Flow

The frontend must handle these events from the `text/event-stream`:

1. **`thinking`**: Emitted instantly to tell the UI the planner is evaluating the prompt.
2. **`tool_selected`**: Contains `"tool"` and `"filters"`. UI should show "Searching database for X...".
3. **`formatting`**: Emitted instantly before calling the LLM formatter. UI should show "Formatting response...".
4. **`tool_result`**: Contains `"result"` (raw JSON from the tool) and `"text"` (LLM natural language summary). UI can render a data card + the text response.
5. **`no_tool`**: Emitted if the planner couldn't match a tool. Contains `"message"`.
6. **`error`**: Emitted if a tool or the LLM failed.
7. **`done`**: Stream closure.

## Test Commands

```
python scripts/test_tool_layer.py
python scripts/test_analytics_tools.py
python scripts/test_api_endpoints.py
python scripts/test_analytics_endpoints.py
python scripts/test_providers.py
python scripts/test_planner.py
python scripts/test_chat_endpoint.py
```

## Current Task

Begin **Phase 4: Frontend Development**.

### Recommended implementation

1. **Initialize Next.js project:** Create `frontend/` directory. Use Next.js with App Router, TailwindCSS, and shadcn/ui.
2. **Setup Fetch/SSE Hooks:** Implement a custom React hook (or use an existing library) to handle the SSE `/chat` endpoint parsing.
3. **Chat Interface:** Build a modern, sleek chat interface (vibrant colors, glassmorphism, dynamic design as per UI instructions).
4. **Tool Result Cards:** When the `tool_result` event fires, map the `result` JSON to a custom React component (e.g., a chart for `yield_statistics` or a grid for `search_reactions`), and display the `text` field as the assistant's dialogue.

## Rules

- Do not regenerate datasets
- Use DuckDB for all data access currently
- Preserve chemistry JSON structures
- Read PROJECT_SPEC.md before making changes
- Update PROJECT_STATE.md, TASKS.md, and AI_HANDOFF.md after major milestones
- Do not introduce vector databases, LangGraph, or agent frameworks yet
