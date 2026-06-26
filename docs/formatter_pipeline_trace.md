# Formatter Pipeline Trace

This trace details the execution path that turns raw tool output into the natural language explanation shown to the user in the Chat UI.

## 1. Trigger
* **Origin:** `frontend/src/components/ChatInterface.tsx`
* **Action:** Upon receiving a successful upload response, the frontend injects the raw `CompareExperimentResponse` into the chat feed as a system message. It then triggers `sendMessage()` with an explicit explanation prompt.
* **Payload:** 
  ```json
  {
    "message": "I just uploaded an experiment (file.json). Please summarize...",
    "tool_result_override": { /* ComparisonReport JSON */ },
    "tool_name_override": "upload_comparison"
  }
  ```

## 2. Stream Orchestrator
* **Module:** `backend/chat/stream.py` -> `stream_chat_events()`
* **Action:** The `/chat` endpoint receives the payload. It detects the presence of `tool_result_override`.
* **Bypass:** The orchestrator *skips* invoking `Planner.plan()`. Instead, it manually constructs a synthetic `PlannerResult`:
  ```python
  result = PlannerResult(
      question=request.message,
      tool="upload_comparison",
      filters={},
      tool_result=request.tool_result_override,
      success=True
  )
  ```
* **Event Yielded:** `tool_selected` (telling the frontend which tool was executed).

## 3. Formatting Dispatch
* **Module:** `backend/chat/formatter.py` -> `format_response()`
* **Action:** The orchestrator invokes the formatter, passing the synthetic `PlannerResult` and the selected Formatter LLM provider (e.g., Groq or Ollama).

## 4. Prompt Construction
* **Module:** `backend/chat/formatter.py`
* **Action:** Constructs a strict two-message context array:
  - **System Prompt:** Instructs the LLM to act as a strict Data Reviewer, prohibiting statistical hallucination and enforcing a specific output structure (`**Observations:**`, `**Data Quality Notes:**`, etc.).
  - **User Prompt:** Contains the user's question, the name of the tool (`upload_comparison`), and a `json.dumps()` of the tool result.

## 5. LLM Execution
* **Module:** `backend/providers/base.py` (Implementation: Groq or Ollama)
* **Action:** The provider sends the messages to the LLM model.
* **Output:** A markdown string adhering to the requested structure.

## 6. SSE Transmission & Rendering
* **Module:** `backend/chat/stream.py` & `frontend/src/services/chat.ts`
* **Action:** The markdown string is packaged into a `tool_result` SSE event and streamed back to the client.
* **Rendering:** `useChatStream.ts` updates the `assistant` message in the UI, rendering the markdown below the structured `ComparisonResultCard`.
