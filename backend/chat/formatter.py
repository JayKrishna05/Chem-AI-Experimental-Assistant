"""Response formatting layer."""

from __future__ import annotations

import json
from typing import Any

from backend.planner.planner import PlannerResult
from backend.providers.base import BaseProvider, Message


def format_response(
    provider: BaseProvider,
    planner_result: PlannerResult,
    model: str | None = None,
) -> str:
    """Format a natural language response from a raw tool payload.
    
    This abstracts the raw JSON structure into human-readable text.
    """
    if not planner_result.success:
        return f"I encountered an error: {planner_result.error}"

    if planner_result.is_no_tool():
        return "I couldn't find a tool to answer that specific question based on my capabilities."

    tool_result = planner_result.tool_result or {}

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
        response = provider.chat(messages, model=model)
        return response.content.strip()
    except Exception as exc:
        return f"Error formatting response: {exc}"
