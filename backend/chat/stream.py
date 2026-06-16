"""SSE Streaming logic for the chat endpoint."""

from __future__ import annotations

import json
from collections.abc import Iterator

from backend.api.models import ChatRequest
from backend.chat.formatter import format_response
from backend.planner import Planner
from backend.providers import get_provider
from backend.utils import sanitize_json


def stream_chat_events(request: ChatRequest) -> Iterator[str]:
    """Execute the planner and yield SSE events for the chat flow."""
    # Obtain provider (using request override if provided)
    provider = get_provider(request.provider)
    
    # Instantiate Planner with the provider
    planner = Planner(provider=provider)

    def emit(event: dict) -> str:
        return f"data: {json.dumps(sanitize_json(event))}\n\n"

    # 1. Emit thinking event
    yield emit({'type': 'thinking'})

    # 2. Run the planner (synchronous)
    result = planner.plan(request.message)

    if not result.success:
        yield emit({'type': 'error', 'message': result.error})
        yield emit({'type': 'done'})
        return

    if result.is_no_tool():
        msg = "I couldn't find a tool to answer that specific question based on my capabilities."
        yield emit({'type': 'no_tool', 'question': request.message, 'message': msg})
        yield emit({'type': 'done'})
        return

    # 3. Emit tool_selected event
    yield emit({'type': 'tool_selected', 'tool': result.tool, 'filters': result.filters})

    # 4. Emit formatting event
    yield emit({'type': 'formatting'})

    # 5. Generate natural language summary using the formatter
    summary_text = format_response(provider, result, model=request.model)

    # 6. Emit tool_result containing raw payload and formatted text
    yield emit({'type': 'tool_result', 'result': result.tool_result, 'text': summary_text})

    # 6. Emit done
    yield emit({'type': 'done'})

