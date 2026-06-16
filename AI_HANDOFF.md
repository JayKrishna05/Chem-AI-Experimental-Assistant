# AI HANDOFF

Date: 2026-06-16

## Current Status

Planner layer completed.

Implemented this milestone:

- `backend/planner/prompts.py` — SYSTEM_PROMPT with tool catalog + 9 few-shot examples
- `backend/planner/schema.py` — per-tool filter schemas + `validate_planner_call()`
- `backend/planner/planner.py` — `Planner` class + `PlannerResult` dataclass
- `backend/planner/__init__.py` — public exports
- `scripts/test_planner.py` — 43 tests, all passing

All prior work remains intact.

## Architecture (Current)

```
Dataset  →  DuckDB  →  Tools  →  FastAPI (10 endpoints)

Provider Layer
  BaseProvider → OllamaProvider (live) / stubs

Planner Layer (NEW)
  User question
    ↓
  Planner.plan(question)
    ↓
  LLM (via provider.chat)
    ↓
  JSON extraction (brace-balanced scanner)
    ↓
  validate_planner_call() — strict schema check
    ↓
  Tool dispatch (_TOOL_DISPATCH)
    ↓
  PlannerResult
```

Not yet implemented:

```
POST /chat      ← NEXT (SSE streaming)
frontend/       ← Phase 4
```

## Planner Layer

### How to use

```python
from backend.providers import get_provider
from backend.planner import Planner

planner = Planner(provider=get_provider())
result = planner.plan("Which catalysts are most common in Buchwald-Hartwig reactions?")

if result.success and not result.is_no_tool():
    print(result.tool)          # "catalyst_statistics"
    print(result.filters)       # {"reaction_type": "Buchwald-Hartwig"}
    print(result.tool_result)   # {"tool": "catalyst_statistics", "results": [...], ...}
elif result.is_no_tool():
    print("No tool matched the question.")
else:
    print("Error:", result.error)
```

### Files

| File | Purpose |
|---|---|
| `prompts.py` | `SYSTEM_PROMPT` — tool catalog, filter schemas, format rules, 9 few-shot examples |
| `schema.py` | `TOOL_FILTER_SCHEMAS`, `KNOWN_TOOLS`, `validate_planner_call()`, `PlannerValidationError` |
| `planner.py` | `Planner`, `PlannerResult`, `_TOOL_DISPATCH`, JSON extraction |
| `__init__.py` | Public exports: `Planner`, `PlannerResult`, `KNOWN_TOOLS`, `NO_TOOL`, `PlannerValidationError` |

### PlannerResult fields

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | True if a tool was called or `__none__` was returned |
| `question` | `str` | Original user question |
| `tool` | `str \| None` | Selected tool name (or `"__none__"` or `None` on error) |
| `filters` | `dict` | Validated, coerced filter parameters |
| `tool_result` | `dict \| None` | Raw return value from the tool function |
| `raw_llm_response` | `str` | Full LLM text response (for debugging) |
| `error` | `str \| None` | Human-readable error if `success=False` |
| `retried` | `bool` | True if a retry was needed |

### Design decisions

- One retry on parse/validation failure with an explicit correction prompt
- JSON extraction uses a brace-balanced character scanner — handles nested `"filters": {}`
- All 9 tools are in `_TOOL_DISPATCH`; an import-time check prevents drift
- Planner never raises — all failures are `PlannerResult(success=False)`
- `__none__` sentinel: the LLM outputs this when no tool fits the question

### Available tools (KNOWN_TOOLS)

```
search_reactions        search_procedures       molecule_lookup
catalyst_statistics     yield_statistics        temperature_statistics
source_dataset_statistics  reaction_type_statistics  dataset_summary
```

## FastAPI Endpoints (Complete)

Retrieval: `GET /health`, `/reactions/search`, `/procedures/search`, `/molecules/search`

Analytics: `GET /analytics/catalysts`, `/analytics/yields`, `/analytics/temperatures`,
`/analytics/datasets`, `/analytics/reaction-types`, `/analytics/summary`

## Test Commands

```
python scripts/test_tool_layer.py
python scripts/test_analytics_tools.py
python scripts/test_api_endpoints.py
python scripts/test_analytics_endpoints.py
python scripts/test_providers.py
python scripts/test_planner.py
```

## Current Task

Build `POST /chat` — the streaming chat endpoint.

### Recommended implementation

#### 1. FastAPI SSE chat endpoint (`backend/api/routes.py` or new `chat_routes.py`)

```python
POST /chat
Body: {"message": str, "provider": str | None, "model": str | None}
Response: text/event-stream (SSE)
```

SSE event format:
```
data: {"type": "tool_selected", "tool": "search_reactions", "filters": {...}}

data: {"type": "tool_result", "result": {...}}

data: {"type": "done"}
```

#### 2. Streaming flow

```
POST /chat
  → Planner.plan(message)        [fast, ~1s]
  → stream: tool_selected event
  → stream: tool_result event    [contains raw tool data]
  → stream: done event
```

The planner runs synchronously (it is already fast). The streaming is
about keeping the client informed in real time, not about streaming
token-by-token from the LLM (that is a Phase 5 enhancement).

#### 3. Pydantic models needed

```python
class ChatRequest(BaseModel):
    message: str
    provider: str | None = None   # overrides ORD_PROVIDER env var
    model: str | None = None      # overrides ORD_PLANNER_MODEL env var

# Response is SSE — no Pydantic response model
```

#### 4. Error handling in SSE

If the planner returns `success=False` or `is_no_tool()`:
```
data: {"type": "no_tool", "question": "...", "message": "I couldn't find a tool for that question."}

data: {"type": "done"}
```

If a provider error occurs:
```
data: {"type": "error", "message": "LLM error: ..."}

data: {"type": "done"}
```

#### 5. Critical rules

- Still no agents, no multi-step planning
- The planner runs once per chat message
- FastAPI SSE uses `fastapi.responses.StreamingResponse` with `media_type="text/event-stream"`
- Each SSE event is formatted as `data: <json>\n\n`
- Add `POST /chat` smoke test to `scripts/test_chat_endpoint.py`

## Known Data Notes

- `yield_statistics(reaction_type="Suzuki")` returns zero procedure records — normalized procedure reaction types in this dataset do not include "Suzuki". The planner handles this gracefully: `success=True`, `tool_result["count"] == 0`.

## Rules

- Do not regenerate datasets
- Use DuckDB for all data access
- Preserve chemistry JSON structures
- Read PROJECT_SPEC.md before making changes
- Update PROJECT_STATE.md, TASKS.md, and AI_HANDOFF.md after major milestones
- Do not introduce vector databases, LangGraph, or agent frameworks
