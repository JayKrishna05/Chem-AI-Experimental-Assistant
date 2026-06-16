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
    timeout: float = 15.0,
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
        "Do not invent information or mention the underlying JSON structure."
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

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(provider.chat, messages, model=model)
            response = future.result(timeout=timeout)
            return response.content.strip()
    except concurrent.futures.TimeoutError:
        return "The response formatting timed out."
    except Exception as exc:
        return f"Error formatting response: {exc}"
