# AI HANDOFF

Date: 2026-06-16

## Current Status

Provider abstraction layer completed.

Implemented this milestone:

- `backend/providers/base.py` — `BaseProvider` ABC, `Message`, `ChatResponse`, `GenerateResponse`
- `backend/providers/config.py` — `ProviderConfig` dataclass + `load_config()` from env vars
- `backend/providers/ollama_provider.py` — live Ollama REST API (stdlib urllib, no extra dep)
- `backend/providers/openai_provider.py` — documented stub
- `backend/providers/anthropic_provider.py` — documented stub
- `backend/providers/gemini_provider.py` — documented stub
- `backend/providers/provider_factory.py` — `get_provider()` + `SUPPORTED_PROVIDERS`
- `backend/providers/__init__.py` — public exports
- `scripts/test_providers.py` — 27 tests, all passing (incl. live Ollama round-trips)

All prior work remains intact.

## Architecture (Current)

```
Dataset  →  DuckDB  →  Tools  →  FastAPI (10 endpoints)
                                        ↑
                                  Provider Layer (NEW)
                                  BaseProvider
                                  OllamaProvider (live)
                                  OpenAIProvider (stub)
                                  AnthropicProvider (stub)
                                  GeminiProvider (stub)
                                  provider_factory.get_provider()
```

Not yet implemented:

```
backend/planner/    ← NEXT
POST /chat          ← after planner
frontend/           ← Phase 4
```

## Provider Layer

### How to use

```python
from backend.providers import get_provider, Message

provider = get_provider()           # reads ORD_PROVIDER env var
response = provider.chat([
    Message(role="system", content="You are a chemistry assistant."),
    Message(role="user", content="What temperature does Buchwald-Hartwig typically run at?"),
])
print(response.content)
```

### Configuration (env vars)

| Variable | Default | Description |
|---|---|---|
| `ORD_PROVIDER` | `ollama` | Active provider |
| `ORD_PLANNER_MODEL` | `qwen2.5:3b` | Model for intent/tool selection |
| `ORD_ANALYSIS_MODEL` | ← planner_model | Model for summarisation (falls back) |
| `ORD_OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server URL |
| `ORD_OPENAI_API_KEY` | — | OpenAI key (stub, not implemented) |
| `ORD_ANTHROPIC_API_KEY` | — | Anthropic key (stub, not implemented) |
| `ORD_GEMINI_API_KEY` | — | Gemini key (stub, not implemented) |

### Key design decisions

- Business logic must call `get_provider()` only — never import concrete classes
- `OllamaProvider` uses Python stdlib `urllib` — no extra HTTP library needed
- `stream=False` — responses arrive as a single JSON object (streaming is Phase 3 chat endpoint work)
- Stubs raise `NotImplementedError` at call time; missing API keys raise `ValueError` at init time
- Adding a new provider requires only one line in `_PROVIDER_REGISTRY` in `provider_factory.py`

## FastAPI Endpoints (Complete)

Retrieval:
- `GET /health`
- `GET /reactions/search`
- `GET /procedures/search`
- `GET /molecules/search`

Analytics:
- `GET /analytics/catalysts`
- `GET /analytics/yields`
- `GET /analytics/temperatures`
- `GET /analytics/datasets`
- `GET /analytics/reaction-types`
- `GET /analytics/summary`

## Tool Layer (Complete)

Retrieval (`backend/tools/chemistry_tools.py`):
- `search_reactions()`, `search_procedures()`, `molecule_lookup()`

Analytics (`backend/tools/analytics_tools.py`):
- `catalyst_statistics()`, `yield_statistics()`, `temperature_statistics()`
- `source_dataset_statistics()`, `reaction_type_statistics()`, `dataset_summary()`

## Test Commands

```
python scripts/test_tool_layer.py
python scripts/test_analytics_tools.py
python scripts/test_api_endpoints.py
python scripts/test_analytics_endpoints.py
python scripts/test_providers.py
```

## Current Task

Build the planner layer.

### Recommended implementation

Create `backend/planner/`:

- `planner.py` — `Planner` class:
  - Takes a `BaseProvider` (for the planner model) and the tool registry
  - Receives a user message string
  - Sends a prompt to the LLM asking it to output a JSON DSL call
  - Validates the JSON against the tool registry
  - Dispatches to the appropriate tool function
  - Returns the structured tool result

- `prompts.py` — System prompts and few-shot examples for the planner

- `__init__.py` — Public exports

The JSON DSL format (from PROJECT_SPEC.md):
```json
{
  "tool": "search_reactions",
  "filters": {
    "reaction_type": "Buchwald-Hartwig",
    "yield_min": 80
  }
}
```

### Critical rules

- Planner + Tools only — no autonomous agents
- The LLM output must be validated (parse JSON, check tool name) before dispatch
- If the LLM output is not valid JSON, retry once then return an error
- Reuse existing DuckDB tool and analytics functions directly
- Do not add vector databases, LangGraph, or agent frameworks

## Known Data Notes

- `yield_statistics(reaction_type="Suzuki")` returns zero procedure records — normalized procedure reaction types in this dataset do not include "Suzuki". The planner should handle empty results gracefully and broaden filters.

## Rules

- Do not regenerate datasets
- Use DuckDB for all data access
- Preserve chemistry JSON structures
- Read PROJECT_SPEC.md before making changes
- Update PROJECT_STATE.md, TASKS.md, and AI_HANDOFF.md after major milestones
- Do not introduce vector databases, LangGraph, or agent frameworks
