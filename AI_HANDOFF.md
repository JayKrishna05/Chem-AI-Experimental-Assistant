# AI HANDOFF

Date: 2026-06-16

## Current Status

Phase 4 Frontend completed. `Next.js` chat interface with `SSE streaming` is finished.

Implemented this milestone:

- `frontend/src/app/page.tsx` — Root application page rendering the ChatInterface.
- `frontend/src/hooks/useChatStream.ts` — React hook parsing the SSE text/event-stream.
- `frontend/src/types/chat.ts` — Types for SSE events and Chat Messages.
- `frontend/src/components/ChatInterface.tsx` — Main chat layout wrapper.
- `frontend/src/components/ChatStream.tsx` — Message list container.
- `frontend/src/components/ChatMessage.tsx` — Individual message bubble.
- `frontend/src/components/ChatInput.tsx` — User input box.
- `frontend/src/components/ToolResultCard.tsx` — Collapsible card for rendering `tool_result` structured JSON.
- `frontend/src/components/StatusIndicator.tsx` — Loading indicators for `thinking`, `tool_selected`, and `formatting`.
- `backend/utils.py` — `sanitize_json` utility created and applied to all DB retrieval and SSE outputs to convert `NaN` and `Infinity` into `null` (None), ensuring RFC-compliant JSON parsing on the frontend.
- **Model Management**: Added model retrieval API (`GET /models`, `GET /models/current`, `POST /models/current`) and global `active_models` state in `backend/api/state.py`.
- **Frontend Model Switcher**: Added `useModels.ts` hook and modified `ChatInterface.tsx` to include dropdown selectors for dynamic switching of both the `planner` and `formatter` models.

All prior backend work remains intact. 

## Architecture (Current)

```
Dataset  →  DuckDB  →  Tools  →  FastAPI (11 endpoints including /chat)

Provider Layer
  BaseProvider → OllamaProvider (live) / stubs

Planner Layer
  User question → Planner.plan(question) → JSON extraction → Tool dispatch → PlannerResult

Chat Layer
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

Frontend Layer (NEW)
  Next.js 15 (App Router) → TailwindCSS + shadcn/ui
  Hook: useChatStream (manages POST /chat)
  Component: ChatInterface (glues everything)
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

Inside `frontend/`:
```
npm run lint
npm run build
```

## Current Task

Begin **Phase 5: Experiment comparison engine and file upload workflow**.

### Recommended implementation

1. **File Upload UI:** Add file upload capability (PDF, DOCX, TXT, CSV, JSON, XLSX) in the chat frontend.
2. **Analysis Endpoint:** Create a new backend endpoint `POST /analyze` to process uploads.
3. **Extraction & Comparison:** Connect the file upload to the planner or a specialized comparison pipeline.

## Rules

- Do not regenerate datasets
- Use DuckDB for all data access currently
- Preserve chemistry JSON structures
- Read PROJECT_SPEC.md before making changes
- Update PROJECT_STATE.md, TASKS.md, and AI_HANDOFF.md after major milestones
- Do not introduce vector databases, LangGraph, or agent frameworks yet
