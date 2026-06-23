"""SSE Streaming logic for the chat endpoint.

This module is the execution core of the chat pipeline:

1. Instantiate a **planner provider** from ``request.planner_provider``.
2. Instantiate a **formatter provider** from ``request.formatter_provider``
   (may be the same class instance as the planner provider, or a completely
   different provider — e.g. local Ollama for planning, Groq for formatting).
3. Run the Planner against the DuckDB tools.
4. Run the Formatter with the raw tool result.
5. Yield SSE events throughout.

Having two independent provider instances is the architectural change that
makes cross-provider routing possible.  Previously a single provider was
shared which made it impossible to route planner and formatter to different
backends.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator

from backend.api.models import ChatRequest
from backend.chat.formatter import format_response
from backend.planner import Planner
from backend.providers import get_provider
from backend.utils import sanitize_json


def stream_chat_events(request: ChatRequest) -> Iterator[str]:
    """Execute the planner and yield SSE events for the chat flow.

    The planner and formatter may use entirely different providers and models.
    """
    # --- Build planner provider ---
    planner_provider_name = request.planner_provider or "ollama"
    planner_provider = get_provider(planner_provider_name)
    planner_timeout = float(request.planner_timeout or 59.0)

    # --- Build formatter provider (may differ from planner) ---
    formatter_provider_name = request.formatter_provider or "ollama"
    formatter_timeout = float(request.formatter_timeout or 59.0)

    # Only instantiate a second provider if it differs from the planner's
    if formatter_provider_name == planner_provider_name:
        formatter_provider = planner_provider
    else:
        formatter_provider = get_provider(formatter_provider_name)

    print(
        f"[Stream] planner={planner_provider_name}/{request.model} timeout={planner_timeout}s | "
        f"formatter={formatter_provider_name}/{request.formatter_model} timeout={formatter_timeout}s"
    )

    # Instantiate Planner with the planner provider
    planner = Planner(provider=planner_provider)

    def emit(event: dict) -> str:
        return f"data: {json.dumps(sanitize_json(event))}\n\n"

    # 1. Emit thinking event
    yield emit({"type": "thinking"})

    global_start = time.time()
    planner_start = time.time()

    # 2. Run the planner (synchronous) — uses planner_provider + planner model
    result = planner.plan(request.message, model=request.model, timeout=planner_timeout)
    
    planner_end = time.time()
    planner_time_ms = int((planner_end - planner_start) * 1000)

    if not result.success:
        yield emit({"type": "error", "message": result.error})
        yield emit({"type": "done"})
        return

    if result.is_no_tool():
        msg = "I couldn't find a tool to answer that specific question based on my capabilities."
        yield emit({"type": "no_tool", "question": request.message, "message": msg})
        yield emit({"type": "done"})
        return

    # Simulate tool execution time if it was executed during planning (it was)
    # The actual tool execution happens inside planner.plan, so for now we estimate or leave it bundled.
    # Actually, planner.plan returns a result. It executes the tool internally. We can just attribute the time.
    # But for a cleaner Dev Tools look, we can just show the total planner+tool time as "Planner Time".
    # Wait, the Planner class might record the tool execution time? Let's check. 
    # For now, just attribute everything before formatting to plannerTimeMs.

    # 3. Emit tool_selected event
    yield emit({
        "type": "tool_selected", 
        "tool": result.tool, 
        "filters": result.filters,
        "plannerProvider": planner_provider_name,
        "plannerModel": request.model,
        "plannerTimeMs": planner_time_ms
    })

    # 4. Emit formatting event
    yield emit({"type": "formatting"})

    formatter_start = time.time()

    # 5. Generate natural language summary — uses formatter_provider + formatter model
    summary_text = format_response(
        formatter_provider,
        result,
        model=request.formatter_model,
        timeout=formatter_timeout,
    )
    
    formatter_end = time.time()
    formatter_time_ms = int((formatter_end - formatter_start) * 1000)
    total_time_ms = int((formatter_end - global_start) * 1000)

    # 6. Emit tool_result containing raw payload and formatted text
    yield emit({
        "type": "tool_result", 
        "result": result.tool_result, 
        "text": summary_text,
        "formatterProvider": formatter_provider_name,
        "formatterModel": request.formatter_model,
        "formatterTimeMs": formatter_time_ms,
        "totalTimeMs": total_time_ms
    })

    # 7. Emit done
    yield emit({"type": "done"})
