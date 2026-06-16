"""Response formatting layer."""

from __future__ import annotations

import json
import concurrent.futures
from typing import Any

from backend.planner.planner import PlannerResult
from backend.providers.base import BaseProvider, Message


def format_response(
    provider: BaseProvider,
    planner_result: PlannerResult,
    model: str | None = None,
    timeout: float = 59.0,
) -> str:
    """Format a natural language response from a raw tool payload.
    
    This abstracts the raw JSON structure into human-readable text.
    """
    if not planner_result.success:
        return f"I encountered an error: {planner_result.error}"

    if planner_result.is_no_tool():
        return "I couldn't find a tool to answer that specific question based on my capabilities."

    raw_result = planner_result.tool_result or {}
    tool_result = dict(raw_result)

    # Truncate large lists to prevent context window overflow
    for key, value in list(tool_result.items()):
        if isinstance(value, list) and len(value) > 5:
            tool_result[key] = value[:5]
            tool_result[f"_{key}_note"] = f"Truncated from {len(value)} to 5 items for summarization."

    sys_prompt = (
        "You are an expert chemistry AI assistant. "
        "A user asked a question, and a backend tool was executed to answer it. "
        "Your task is to summarize the raw JSON output into a natural, conversational response. "
        "Focus on the most important numbers, findings, or trends. "
        "If the tool found zero results or no data, state that clearly. "
        "Do not invent information or mention the underlying JSON structure. "
        "IMPORTANT: If the JSON contains both 'statistics' and 'clean_statistics', "
        "prefer 'clean_statistics' as it filters out extreme outliers and uses chemically "
        "meaningful ranges (yields 0-100%, temperatures -100°C to 300°C). "
        "If clean_statistics has far fewer records than the total, mention the data quality issue. "
        "Always report average, median, min, and max from clean_statistics when available."
    )

    user_content = (
        f"Question: {planner_result.question}\n\n"
        f"Tool Used: {planner_result.tool}\n\n"
        f"Raw Output:\n{json.dumps(tool_result, indent=2)}"
    )

    messages = [
        Message(role="system", content=sys_prompt),
        Message(role="user", content=user_content),
    ]

    import time
    from backend.api.state import active_models
    
    start_time = time.time()
    prompt_size = len(sys_prompt) + len(user_content)
    
    print(f"[Formatter Request] Planner model: {active_models.get('planner_model')}, Formatter model: {model}, Configured timeout: {timeout}, Prompt size: {prompt_size} chars")

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(provider.chat, messages, model=model, timeout=timeout)
            response = future.result(timeout=timeout)
            duration = time.time() - start_time
            print(f"[Formatter Success] Response size: {len(response.content)} chars, Duration: {duration:.2f}s")
            return response.content.strip()
    except Exception as exc:
        duration = time.time() - start_time
        err_type = type(exc).__name__
        print(f"[Formatter Failure] Duration: {duration:.2f}s, Reason: {err_type}: {exc}")
        
        # Fallback summary
        try:
            res_count = tool_result.get("count", len(tool_result.get("results", [])) if "results" in tool_result else "an unknown number of")
            return f"I found {res_count} matching records using {planner_result.tool}. The summary model failed to respond before the timeout or encountered an error. The raw results remain available below."
        except Exception:
            return f"Formatting failed. The raw results remain available below."
