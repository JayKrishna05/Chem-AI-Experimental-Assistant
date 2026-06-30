# Current Architecture Review

## Overview
The ORD Experimental Intelligence Assistant has reached the end of Phase 6, featuring a robust multi-provider LLM backend and a modern Next.js React frontend. The system acts as a conversational interface for a large DuckDB dataset (2.3M+ reactions).

## Current Architecture

### 1. Data Layer
*   **DuckDB**: Central immutable data store containing `reactions`, `procedures`, and `molecules`.
*   **No Persistence**: Uploaded datasets are evaluated in memory and discarded.

### 2. Backend (FastAPI)
*   **Planner (`planner.py`)**: Uses a few-shot prompt system to translate natural language into a JSON DSL. Selects one of 10 available tools. It includes fallback retries for hallucinated outputs.
*   **Tools (`analytics_tools.py`)**: Executes complex DuckDB SQL queries. Currently, tools both fetch the data and heavily format it into UI-ready JSON contracts (acting as both Repository and View-Model).
*   **Formatter (`chemistry_formatter.py`)**: Consumes the raw JSON output from tools and translates it into human-readable Markdown via an LLM.
*   **Provider Factory**: Supports dual-provider architecture (e.g., local Ollama for the Planner, Groq for the Formatter).

### 3. Frontend (Next.js)
*   **Chat Interface**: Real-time SSE streaming chat with specific Markdown rendering capabilities.
*   **Upload Pipeline**: Client-side dropzone validating files before transmitting them via decoupled services (`upload.ts`, `api.ts`).

## Component Workflows

*   **Data Flow**: User Input -> Next.js -> FastAPI (`/api/chat`) -> Planner LLM -> Tool Selection -> DuckDB -> Tool Execution -> Formatter LLM -> SSE Stream -> Next.js UI.
*   **Planner Workflow**: Accepts `ChatRequest`, routes to the Provider, extracts `{tool, filters}` via brace-matching, validates against `schema.py`, and triggers the specific Python function.
*   **Upload Workflow**: `POST /experiments/compare` accepts multipart form data. The parser dynamically dispatches (CSV, JSON, XLSX, Text) to generate a `CanonicalExperiment`. This is normalized and validated before being passed to the `ComparisonService`.
*   **Comparison Workflow**: Heuristically matches the validated `CanonicalExperiment` against DuckDB historical data. It performs similarity matching, optimal condition checking, and temperature anomaly profiling.
*   **Formatter Workflow**: Bypassed entirely for direct uploads (`tool_result_override`), but typically takes the Tool Result JSON and applies a final conversational pass.

## Key Observations
The architecture successfully bridges the LLM / deterministic database divide. However, the lack of a formal Data Access Layer (DAL) heavily couples business logic to the UI tool contracts, hindering the evolution of the `ComparisonService`.
