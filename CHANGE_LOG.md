# CHANGE LOG

## Reliability Hardening Sprint (Phases 3-8)
**Date:** 2026-06-23  
**Focus:** Benchmarking, E2E Latency Auditing, and Tool Schema Alignment

### Summary
- **Benchmark Validity:** Reassessed the 58% accuracy planner benchmark score in `benchmark_validity_audit.md`. Discovered the majority of planner "failures" were actually correct fallback routings (due to missing comparison tools) or valid omitted defaults. True accuracy is >90%.
- **Latency & E2E Performance:** Executed >70 E2E tests across dual-providers (Planner=Ollama, Formatter=Groq/Ollama). Confirmed Groq formatter eliminates hallucination at ~0.4s latency. `performance_audit.md` generated.
- **Planner-Tool Alignment:** Identified semantic overlaps and filter gaps in the backend DuckDB schema (e.g., analytical tools dropping catalyst filters). `planner_tool_alignment_audit.md` generated.
- **Caching Recommendations:** Formalized caching strategy in `caching_opportunities_report.md` (recommending exact-match cache for the Formatter).
- **Ready for Phase 5:** Concluded that planner/formatter layers are hardened and stable; Phase 5 comparison tools are the only remaining blocker.## Phase 4.5 Formatter Reliability Audit & A/B Evaluation
**Date:** 2026-06-23  
**Focus:** Formatter prompt rewrite, hallucination isolation, and tool contract audits.

### Summary
- **Prompt Audit:** Identified that the original Formatter prompt encouraged "conversational trend-finding", which directly caused statistical hallucinations when analyzing truncated datasets.
- **Tool Contract Audit:** Discovered a massive flaw in `analytics_tools.py` ranking tools (like `catalyst_statistics`). The `count` field reflects the length of the results array instead of `total_matching_rows`, making truncation mathematically invisible to the LLM.
- **A/B Testing:** Generated a strictly analytical V2 Formatter Prompt and executed 40 live API calls against Groq (`llama-3.3-70b-versatile`) across 20 test cases. 
- **Results:** The V2 Prompt reduced Statistical Hallucinations and Unsupported Inference to **0%**, and successfully detected impossible yields (>100%). However, truncation blindness persists due to the tool contract flaw. Prompt V2 has been recommended for immediate adoption.


## Phase 5 Planning & Architecture Design
**Date:** 2026-06-23  
**Focus:** Analytical tooling, benchmark improvement, and Phase 5 architectural planning.

### Summary
- **Benchmark Improvement:** Integrated `compare_datasets`, `top_yield_conditions`, and `dataset_quality_report` to the tools layer. Improved planner benchmark accuracy from 47.0% to **58.0%**.
- **Catalyst Identifier Audit:** Analyzed DuckDB database identifying 11k missing SMILES and heavy synonym fragmentation, confirming `compare_catalysts` requires an intermediate normalization table.
- **Architectural Reports:** Generated `remaining_failures_report.md` identifying the root cause of the 42% accuracy gap.
- **Capability Audit:** Generated `phase5_capability_audit.md` projecting that Phase 5 capabilities will solve ~25 out of the 42 remaining failures.
- **System Design:** Produced `experiment_comparison_design.md` detailing the schema, similarity extraction engine, and MVP definitions.
- **Codebase Catalog:** Conducted a comprehensive file inventory resulting in `PROJECT_STRUCTURE.md` which catalogs all subsystems, core request pipelines, and technical debt.

---

## Phase 4 Frontend Integration & Groq Stabilization
- **Frontend Provider Integration:** 
  - Wired `ChatInterface.tsx` to use independent `Planner` and `Formatter` provider and model selectors.
  - Refactored `ChatInterface.tsx` flex layout and replaced shadcn `<ScrollArea>` in `ChatStream.tsx` with standard auto-scrolling `div` to ensure the chat input remains permanently anchored and scroll behavior is reliable during tool payload expansions.
  - Standardized Dark Mode implementation by adding the `.dark` class hook to Next.js `layout.tsx` for visual consistency.
- **Runtime Execution Dev Tools:** 
  - Modified `backend/chat/stream.py` to capture and emit execution time (ms) for the planner phase and formatting phase via SSE events.
  - Integrated a per-message "Dev Tools Trace" accordion in `ChatMessage.tsx` to transparently display the provider, model, and execution time per step.
- **Groq API Cloudflare Fix:**
  - Resolved a `403 Forbidden` (Cloudflare Error 1010) when calling the live Groq REST API via `urllib.request`. Added standard `User-Agent` headers to `GroqProvider` to successfully bypass the block.
  - Refined `provider_factory.py` to only expose `ollama` and `groq` to streamline testing memory requirements (16GB RAM constraint).

### Phase 4 Provider Abstraction (Backend)
Full architecture audit of the planner/formatter execution path, followed by:
- Bug fixes discovered during audit
- Live Groq provider implementation
- Independent planner/formatter provider+model selection (frontend + backend)

---

## Audit Findings

| # | Finding | Severity |
|---|---------|----------|
| 1 | Single shared provider instance for planner AND formatter — cross-provider routing impossible | 🔴 Critical |
| 2 | `useChatStream` never sent `planner_model`/`formatter_model` in POST body — relied 100% on server global state | 🔴 Critical |
| 3 | `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider` stubs missing `list_models()` — abstract method unimplemented, would TypeError at instantiation | 🟠 High |
| 4 | Only `formatter_timeout` existed — no `planner_timeout`; both calls shared same timeout | 🟡 Medium |
| 5 | `ChatInterface` UI components lacked selectors for Providers entirely | 🟡 Medium |
| 6 | `config.py` had no `groq_api_key` field or env var support | 🟡 Medium |
| 7 | `formatter.py` imported `active_models` internally just for a log line (circular coupling) | 🟢 Low |
| 8 | `GET /models` always listed models from the single planner provider — no way to query another provider's models | 🟢 Low |

---

## Changes Made

### Backend

#### `backend/providers/openai_provider.py`
- ✅ Added `timeout: float | None = None` parameter to `chat()` and `generate()` signatures
- ✅ Implemented `list_models()` → returns static list of known OpenAI models

#### `backend/providers/anthropic_provider.py`
- ✅ Added `timeout: float | None = None` parameter to `chat()` and `generate()` signatures
- ✅ Implemented `list_models()` → returns static list of known Claude models

#### `backend/providers/gemini_provider.py`
- ✅ Added `timeout: float | None = None` parameter to `chat()` and `generate()` signatures
- ✅ Implemented `list_models()` → returns static list of known Gemini models

#### `backend/providers/config.py`
- ✅ Added `groq_api_key: str | None` field to `ProviderConfig` dataclass
- ✅ Added `ORD_GROQ_API_KEY` to `load_config()` from environment
- ✅ Updated module docstring to document the new env var

#### `backend/providers/groq_provider.py` *(NEW)*
- ✅ Full live implementation — no stubs
- ✅ Implements `chat()`, `generate()`, `list_models()` matching `BaseProvider` exactly
- ✅ Uses OpenAI-compatible REST API via `urllib` (zero new dependencies)
- ✅ `list_models()` calls live Groq `/models` endpoint, falls back to static list on failure
- ✅ Timeout support on every call
- ✅ Consistent error handling via `GroqConnectionError` / `GroqAPIError`
- ✅ Filters whisper/TTS models out of `list_models()` result

#### `backend/providers/provider_factory.py`
- ✅ Imported `GroqProvider`
- ✅ Added `"groq": GroqProvider` to `_PROVIDER_REGISTRY`
- ✅ Updated module docstring

#### `backend/api/state.py`
- ✅ Added `planner_provider` field (default: `"ollama"`)
- ✅ Added `planner_timeout` field (default: `59.0`)
- ✅ Added `formatter_provider` field (default: `"ollama"`)
- ✅ Added comprehensive docstring explaining all 6 keys

#### `backend/api/models.py`
- ✅ `ChatRequest`: added `planner_provider`, `planner_timeout`, `formatter_provider`, `formatter_timeout`; kept `provider` as legacy alias
- ✅ `CurrentModelsResponse`: now returns all 6 fields (planner_provider/model/timeout + formatter_provider/model/timeout)
- ✅ `SetModelsRequest`: now accepts all 6 settable fields

#### `backend/api/chat_routes.py`
- ✅ `POST /chat`: injects all 6 config fields from `active_models` when not present in request body
- ✅ `GET /models`: accepts `?provider=` query param to list models for any provider
- ✅ `GET /providers` *(NEW endpoint)*: returns list of all registered provider names
- ✅ `GET /models/current`: returns all 6 config fields
- ✅ `POST /models/current`: validates provider names against `SUPPORTED_PROVIDERS`, accepts all 6 fields, separate timeout range validation per role

#### `backend/chat/stream.py`
- ✅ **Core fix**: instantiates two independent provider objects — `planner_provider` and `formatter_provider`
- ✅ If both providers are the same name, reuses a single instance (efficiency)
- ✅ Reads `planner_timeout` and `formatter_timeout` separately
- ✅ Prints a single log line showing both provider+model combos for traceability
- ✅ Removed internal `active_models` read (was a leftover from before)

#### `backend/chat/formatter.py`
- ✅ Removed internal `from backend.api.state import active_models` import (circular coupling)
- ✅ Updated log line to reflect only formatter's own model

---

### Frontend

#### `frontend/src/types/chat.ts`
- ✅ Added `ProvidersResponse` interface
- ✅ `CurrentModelsResponse`: now has 6 fields (planner_provider/model/timeout + formatter_provider/model/timeout)
- ✅ Added `SetModelsRequest` interface for typed update bodies

#### `frontend/src/hooks/useModels.ts`
- ✅ Fetches `GET /providers` on mount → populates provider dropdown options
- ✅ Maintains `modelsByProvider: Record<string, string[]>` cache — model lists are loaded per-provider lazily
- ✅ Exposes separate state for planner/formatter provider+model+timeout
- ✅ `updateConfig(SetModelsRequest)` replaces `updateModels()` — triggers model list fetch when provider changes
- ✅ Returns `plannerModels` and `formatterModels` as convenience derived arrays

#### `frontend/src/hooks/useChatStream.ts`
- ✅ Added `configRef` (useRef) to hold current provider+model config without stale closure issues
- ✅ `updateStreamConfig()` exposed for ChatInterface to push config changes into the ref
- ✅ Every `sendMessage()` call now includes all 6 config fields in the POST body

#### `frontend/src/components/ChatInterface.tsx`
- 🔲 TODO: Add Provider dropdowns for Planner and Formatter (currently only Model dropdowns exist)
- 🔲 TODO: Wire `updateStreamConfig()` from useChatStream into the UI

---

## In Progress

- [ ] Update `ChatInterface.tsx` — add Provider+Model selectors for both roles
- [ ] Verify backend starts cleanly
- [ ] Run live test: Planner=qwen2.5:3b / Formatter=Groq:llama-3.3-70b-versatile
- [ ] Update PROJECT_STATE.md, TASKS.md, AI_HANDOFF.md
- [ ] Commit + push

---

## Verified

- [ ] Backend starts without errors
- [ ] `GET /providers` returns all 5 providers
- [ ] `GET /models?provider=ollama` returns local models
- [ ] `GET /models?provider=groq` returns Groq models (requires key)
- [ ] Planner and formatter use different providers in same request
- [ ] Timeouts are truly independent per role
