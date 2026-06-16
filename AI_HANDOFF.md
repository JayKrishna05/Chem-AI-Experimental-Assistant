# AI HANDOFF

Date: 2026-06-17

## Current Status

Phase 4 complete + **Pre-Phase 5 Capability Audit complete**.

100-question capability audit performed. Score: **87/93 = 93.5%**.

## What Changed This Session

1. **`backend/tools/analytics_tools.py`**
   - `yield_statistics` now returns `clean_statistics` (0-100% yield range only) alongside raw stats.
   - `temperature_statistics` now returns `clean_statistics` (-100°C to 300°C range only) alongside raw stats.
   - New `reagent_statistics` tool added — ranks reagents/solvents by occurrence from `reactions.reagents_json`.

2. **`backend/tools/__init__.py`** — exports `reagent_statistics`.

3. **`backend/planner/schema.py`** — `reagent_statistics` added to `TOOL_FILTER_SCHEMAS`.

4. **`backend/planner/planner.py`** — `reagent_statistics` added to `_TOOL_DISPATCH`.

5. **`backend/planner/prompts.py`** — Completely revised:
   - 10 tools documented (was 9, now includes `reagent_statistics`).
   - IMPORTANT NOTES section about NULL reaction_type prevalence and SMILES molecule names.
   - 35+ worked few-shot examples (was 10).
   - Comparison, ranking, natural language, and edge case patterns all covered.

6. **`backend/chat/formatter.py`** — System prompt updated to prefer `clean_statistics` over raw stats when present.

7. **`frontend/src/components/ChatStream.tsx`** — Empty state replaced with rich UI:
   - 10 clickable suggestion chips dispatch queries immediately on click.
   - Shows "2.4M reactions, 1.8M procedures, 2M molecules" stats.
   - `onSuggestion` prop connects to `ChatInterface` → `sendMessage`.

8. **`scripts/test_audit.py`** — New comprehensive test file with 45 assertions across all categories.

## Architecture (Current)

```
Dataset  →  DuckDB  →  Tools (10 tools)  →  FastAPI (14 endpoints including /chat)

Provider Layer
  BaseProvider → OllamaProvider (live, configurable timeout) / stubs

Planner Layer
  User question → Planner.plan(question) → JSON extraction → Tool dispatch → PlannerResult
  10 tools: search_reactions, search_procedures, molecule_lookup, catalyst_statistics,
            yield_statistics, temperature_statistics, source_dataset_statistics,
            reaction_type_statistics, reagent_statistics, dataset_summary

Chat Layer
  POST /chat (SSE Stream)
    ↓
  emit: {type: "thinking"}
    ↓
  run: Planner.plan()
    ↓
  emit: {type: "tool_selected", tool: "...", filters: {...}}
    ↓
  run: format_response() (LLM summary call with timeout)
    ↓
  emit: {type: "tool_result", result: {...raw...}, text: "...summary..."}
    ↓
  emit: {type: "done"}

Frontend Layer
  Next.js 15 (App Router) → TailwindCSS + shadcn/ui
  Hook: useChatStream (manages POST /chat)
  Component: ChatInterface (glues everything)
  Empty state: 10 suggestion chips → sendMessage
```

## Critical Database Facts (MUST READ)

> **99.97% of reactions have `reaction_type = NULL`**
> - Only 750 reactions have a type label (all Buchwald-Hartwig variants)
> - Searches for "Suzuki", "Heck", "amide coupling" by reaction_type return 0 results
> - The planner handles this: uses catalyst/reactant filters instead for those reaction types
> - This is an ORD dataset characteristic, not a system bug

> **Yield data has extreme outliers** (values up to 9×10¹⁹%)
> - Raw global average yield: ~92 trillion percent (meaningless)
> - `clean_statistics` (0-100% range): avg=63.83%, med=68.30% ← **use this**

> **Temperature data: 81% of records at or below 0°C** (likely default/unset values)
> - Raw global median: 0°C (meaningless)
> - `clean_statistics` (-100°C to 300°C): avg=13.63°C ← **use this**

> **Molecule registry is SMILES-only** — no compound names
> - Ethanol (CCO): 40,408. Acetone (CC(C)=O): 8,364. Benzene (c1ccccc1): 5,331.
> - Caffeine/aspirin not in registry. Planner falls back to `search_procedures` text search.

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
python scripts/test_audit.py          ← NEW: 45-assertion capability audit
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
4. **Reagent analytics expansion:** Per-dataset reagent breakdown, most common solvents per reaction type.
5. **Molecule name lookup:** Pre-seeded table mapping common names (ethanol, acetone, caffeine) to SMILES.

## Rules

- Do not regenerate datasets
- Use DuckDB for all data access currently
- Preserve chemistry JSON structures
- Read PROJECT_SPEC.md before making changes
- Update PROJECT_STATE.md, TASKS.md, and AI_HANDOFF.md after major milestones
- Do not introduce vector databases, LangGraph, or agent frameworks yet
- Always use `clean_statistics` from yield/temperature when summarizing for users
