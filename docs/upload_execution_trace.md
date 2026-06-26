# Upload Execution Trace

This document details the execution path of the experiment upload pipeline from the user dropping a file to the final UI render.

## 1. Upload Submission
* **Responsible Module:** `frontend/src/components/UploadDropzone.tsx` & `useUpload.ts`
* **Input Object:** Raw `File` object (e.g. JSON, CSV, XLSX)
* **Output Object:** `FormData` containing the file
* **Transformation:** UI state changes to `uploading`, triggering progress bar. The `uploadAndCompareExperiment` service method sends a `POST /experiments/compare` request as `multipart/form-data`.

## 2. Request Handling
* **Responsible Module:** `backend/api/routes.py` (`experiments_compare`)
* **Input Object:** HTTP Request with `UploadFile`
* **Output Object:** File binary content, filename, and mime type
* **Transformation:** Routes extract the file bytes and pass them to the parser dispatcher.

## 3. Parser Dispatch
* **Responsible Module:** `backend/experiment/parser/dispatcher.py`
* **Input Object:** Raw binary data
* **Output Object:** List of `CanonicalExperiment` instances
* **Transformation:** The dispatcher matches the mime type or extension to a specific format parser (`parser_json.py`, `parser_csv.py`, etc.). The specific parser reads the binary and instantiates raw `CanonicalExperiment` Pydantic models.

## 4. Normalizer
* **Responsible Module:** `backend/experiment/normalizer.py`
* **Input Object:** Raw `CanonicalExperiment`
* **Output Object:** `CanonicalExperiment` (normalized) and a list of normalized field names.
* **Transformation:** Standardizes reaction types (e.g., "Buchwald hartwig" -> "Buchwald-Hartwig"), trims whitespace from list items, and maps catalyst aliases ("palladium" -> "Pd"). Negative yields are zeroed.

## 5. Validator
* **Responsible Module:** `backend/experiment/validator.py`
* **Input Object:** Normalized `CanonicalExperiment`
* **Output Object:** `ValidationResult` (contains the experiment, an `is_valid` boolean, `warnings` list, and `confidence_score`).
* **Transformation:** Checks bounds (temperature, yield) and ensures mandatory fields (reaction_type, reactants, products) exist. Missing critical fields flag `is_valid = False`. 

## 6. Comparison Service
* **Responsible Module:** `backend/services/comparison_service.py`
* **Input Object:** `ValidationResult`
* **Output Object:** `CompareExperimentResponse` Dictionary
* **Transformation:** 
    - Executes `search_reactions` against the database to find exact matches.
    - Executes `top_yield_conditions` to find the best catalyst and average yield for the given reaction type.
    - Classifies the user's yield against the optimal yield (`Excellent Match`, `Comparable`, `Slightly Below Optimal`, `Suboptimal`).
    - Executes `temperature_statistics` to detect anomalous temperature profiles.
    - Packages all results into a unified dictionary structure.

## 7. Frontend Integration
* **Responsible Module:** `frontend/src/hooks/useUpload.ts`
* **Input Object:** JSON response (`CompareExperimentResponse`)
* **Output Object:** Local UI State Update
* **Transformation:** The `uploadState` transitions to `success`, triggering the green success toast. After 3 seconds, a `finally` block clears the toast and resets the state to `idle`.

## 8. Chat Formatter Bypass
* **Responsible Module:** `frontend/src/components/ChatInterface.tsx` & `backend/chat/stream.py`
* **Input Object:** `CompareExperimentResponse` comparison report
* **Output Object:** SSE Event Stream (Markdown)
* **Transformation:** 
    - The frontend renders the raw JSON as a visual `ComparisonResultCard` by injecting a local system message.
    - The frontend simultaneously issues a POST to `/chat` with a prompt asking for an explanation, BUT includes the comparison report inside `tool_result_override` and sets `tool_name_override` to `"upload_comparison"`.
    - The backend `stream.py` detects the override. It skips the `Planner` entirely and feeds the comparison report directly into the `Formatter`.
    - The `Formatter` streams a natural language explanation of the comparison back to the user via Server-Sent Events (SSE).
