# Upload Integration Audit

This document summarizes the current state of the upload workflow integration between the frontend chat interface and the backend processing pipeline, following the Phase 6 completion and subsequent fixes.

## 1. Overview
The upload pipeline allows users to drag-and-drop CSV, JSON, XLSX, or Text files containing experimental data into the chat interface. The system extracts the data, validates it against established heuristics, and compares it against the ORD historical database to find similarities and anomalies.

## 2. Component Review

### 2.1 Backend Pipeline (`parser` -> `normalizer` -> `validator` -> `comparison_service`)
- **Status:** **STABLE**
- **Findings:** The internal pipeline is robust. It correctly parses different formats and applies standardization. The `comparison_service` successfully invokes DuckDB analysis tools using the normalized experiment data.
- **Improvements Made:** The yield classification was enhanced from a simple boolean `is_suboptimal` to a granular scale (`Excellent Match`, `Comparable`, `Slightly Below Optimal`, `Suboptimal`) to provide more accurate feedback to the user.

### 2.2 Frontend State Management (`useUpload.ts`)
- **Status:** **STABLE**
- **Findings:** Previously, the `uploadState` remained in `"success"` or `"error"` indefinitely, causing the upload toast to hang. 
- **Improvements Made:** The lifecycle was fixed by adding a 3-second `setTimeout` within a `finally` block to guarantee the state resets to `"idle"` and the toast disappears gracefully.

### 2.3 Formatter Bypass Integration (`stream.py` & `useChatStream.ts`)
- **Status:** **STABLE**
- **Findings:** Previously, the frontend would ask the Planner to explain the uploaded results without providing the data, causing the Planner to hallucinate or invoke unrelated tools (like `compare_datasets`).
- **Improvements Made:** The `/chat` payload was extended with `tool_result_override`. The frontend now injects the comparison report directly into the chat stream, completely bypassing the Planner. The Formatter natively consumes the override and generates a highly relevant summary.

### 2.4 Error Handling & Edge Cases
- **Invalid Files:** Files that fail to parse return empty experiments with a `is_valid: False` flag and a warning. The frontend correctly displays the warning toast and the `ComparisonResultCard` shows a red error state.
- **No Database Matches:** If an experiment uses a reactant/product not found in the snapshot, the `total_matching` field correctly reports `0` without causing crashes.

## 3. Remaining Technical Debt & Known Limitations
- **Strict Similarity Matching:** The current `search_reactions` query relies on stringified JSON matching (`ILIKE '%Compound%'`). If a user uploads a synonym not caught by the normalizer, or if the database represents the compound via SMILES instead of text, the match will fail. A future iteration should introduce SMILES-based canonicalization and graph matching.
- **Mock Progress Bar:** The frontend upload progress is simulated via an interval because the native `fetch` API lacks upload progress events. If large file uploads (e.g., >50MB) become common, we may need to migrate to `XMLHttpRequest` or chunked uploads to provide real progress.
