"""SSE Streaming logic for the chat endpoint."""

from __future__ import annotations

import json
from collections.abc import Iterator

from backend.api.models import ChatRequest
from backend.chat.formatter import format_response
from backend.planner import Planner
from backend.providers import get_provider


def stream_chat_events(request: ChatRequest) -> Iterator[str]:
    """Execute the planner and yield SSE events for the chat flow."""
    # Obtain provider (using request override if provided)
    provider = get_provider(request.provider)
    
    # Instantiate Planner with the provider
    planner = Planner(provider=provider)

    # 1. Emit thinking event
    yield f"data: {json.dumps({'type': 'thinking'})}\n\n"

    # 2. Run the planner (synchronous)
    result = planner.plan(request.message)

    if not result.success:
        yield f"data: {json.dumps({'type': 'error', 'message': result.error})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    if result.is_no_tool():
        msg = "I couldn't find a tool to answer that specific question based on my capabilities."
        yield f"data: {json.dumps({'type': 'no_tool', 'question': request.message, 'message': msg})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # 3. Emit tool_selected event
    yield f"data: {json.dumps({'type': 'tool_selected', 'tool': result.tool, 'filters': result.filters})}\n\n"

    # 4. Generate natural language summary using the formatter
    summary_text = format_response(provider, result, model=request.model)

    # 5. Emit tool_result containing raw payload and formatted text
    yield f"data: {json.dumps({'type': 'tool_result', 'result': result.tool_result, 'text': summary_text})}\n\n"

    # 6. Emit done
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
