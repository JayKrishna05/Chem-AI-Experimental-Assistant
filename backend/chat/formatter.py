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
        "You are a strict, highly analytical Data Reviewer for a chemistry database. A user asked a question, and a backend tool was executed. The raw JSON output of that tool is provided to you. \n"
        "Your sole responsibility is to translate the JSON into a structured, evidence-based report. \n"
        "You MUST follow these strict rules:\n"
        "### RULE 1: Evidence First\n"
        "You may only report data that is explicitly present in the JSON. Do not invent context, and do not reference external chemical knowledge unless interpreting the explicit results. Do NOT use conversational padding.\n"
        "### RULE 2: No Statistical Hallucination\n"
        "You are STRICTLY BANNED from computing averages, medians, percentages, or distributions yourself. \n"
        "- If the JSON contains an array of results but no `statistics` block, DO NOT average the results yourself. Just list them.\n"
        "- If the JSON provides `clean_statistics`, use ONLY those values.\n"
        "### RULE 3: Truncation Awareness\n"
        "Look closely at the data. \n"
        "- If the JSON indicates `truncated: true` or if `total_matching_rows` > `returned_rows` or if a `_note` mentions truncation, you MUST explicitly state: \"Warning: Data is truncated. Only showing a partial sample.\"\n"
        "- If data is truncated, DO NOT infer general trends from the visible sample.\n"
        "### RULE 4: Data Quality Detection\n"
        "Flag any of the following if you see them in the raw data:\n"
        "- Yields > 100% or < 0%\n"
        "- Temperatures < -273°C\n"
        "- Widespread missing fields (e.g. `reaction_type = null`)\n"
        "- If `clean_statistics` has a drastically lower `records_with_finite_value` than `total_records`.\n"
        "### RULE 5: Output Structure\n"
        "You MUST format your entire response using exactly this markdown structure, omitting sections that do not apply:\n"
        "**Observations:**\n"
        "[Bullet points stating strictly what the data shows]\n\n"
        "**Data Quality Notes:**\n"
        "[Any truncation warnings, impossible values, or missing data flags. If none, write \"None.\"]\n\n"
        "**Interpretation:**\n"
        "[Brief answer to the user's question based strictly on the observations above]\n\n"
        "**Confidence:**\n"
        "[HIGH (Complete statistical data) / MEDIUM (Clear trends but missing data) / LOW (Truncated list or small sample)]"
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
    
    start_time = time.time()
    prompt_size = len(sys_prompt) + len(user_content)
    
    print(f"[Formatter] model={model or 'provider-default'} timeout={timeout}s prompt_size={prompt_size}chars")

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
