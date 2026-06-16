"""ORD Chemistry Planner.

The planner converts a free-text user question into a deterministic
tool call against the ORD DuckDB database.

Workflow
--------
1. Build a chat prompt: system prompt (tool catalog + examples) + user
   question.
2. Send to the configured LLM provider.
3. Extract the JSON DSL from the response.  If the response contains
   prose around the JSON, isolate the first ``{...}`` block.
4. Validate the DSL against the tool schema (``schema.validate_planner_call``).
5. Dispatch to the matching tool function.
6. Return a structured :class:`PlannerResult`.

If parsing or validation fails, retry once with an explicit correction
prompt.  If the retry also fails, return a :class:`PlannerResult` with
``success=False`` and a human-readable ``error`` message.

Design constraints
------------------
- Planner + Tools only — no agent loops, no LangGraph.
- The LLM picks exactly one tool per call.
- Tool execution is deterministic once the DSL is validated.
- The planner never modifies the DuckDB database.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from backend.providers.base import BaseProvider, Message
from backend.tools import (
    catalyst_statistics,
    dataset_summary,
    molecule_lookup,
    reaction_type_statistics,
    reagent_statistics,
    search_procedures,
    search_reactions,
    source_dataset_statistics,
    temperature_statistics,
    yield_statistics,
)

from .prompts import SYSTEM_PROMPT
from .schema import (
    NO_TOOL,
    KNOWN_TOOLS,
    PlannerValidationError,
    validate_planner_call,
)


# ---------------------------------------------------------------------------
# Tool dispatch table
# ---------------------------------------------------------------------------

# Maps tool name → callable.  Every function here must accept keyword
# arguments matching the filter keys defined in schema.TOOL_FILTER_SCHEMAS.
_TOOL_DISPATCH: dict[str, Callable[..., dict[str, Any]]] = {
    "search_reactions": search_reactions,
    "search_procedures": search_procedures,
    "molecule_lookup": molecule_lookup,
    "catalyst_statistics": catalyst_statistics,
    "yield_statistics": yield_statistics,
    "temperature_statistics": temperature_statistics,
    "source_dataset_statistics": source_dataset_statistics,
    "reaction_type_statistics": reaction_type_statistics,
    "reagent_statistics": reagent_statistics,
    "dataset_summary": dataset_summary,
}

# Sanity-check at import time: every KNOWN_TOOL must have a dispatch entry.
_missing = KNOWN_TOOLS - _TOOL_DISPATCH.keys()
if _missing:  # pragma: no cover
    raise RuntimeError(
        f"TOOL_DISPATCH is missing entries for: {_missing}.  "
        "Update _TOOL_DISPATCH in planner.py."
    )


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class PlannerResult:
    """The outcome of a single planner call.

    Attributes
    ----------
    success:
        ``True`` if the planner successfully called a tool.
    question:
        The original user question.
    tool:
        The tool that was selected, or ``None`` if none matched.
    filters:
        The validated, coerced filters passed to the tool.
    tool_result:
        The structured dict returned by the tool, or ``None``.
    raw_llm_response:
        The raw text content returned by the LLM (for debugging).
    error:
        Human-readable error message if ``success=False``.
    retried:
        ``True`` if a retry was needed to get a valid JSON response.
    """

    success: bool
    question: str
    tool: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    tool_result: dict[str, Any] | None = None
    raw_llm_response: str = ""
    error: str | None = None
    retried: bool = False

    def is_no_tool(self) -> bool:
        """Return True if the planner determined no tool fits the question."""
        return self.tool == NO_TOOL

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict (e.g. for JSON API responses)."""
        return {
            "success": self.success,
            "question": self.question,
            "tool": self.tool,
            "filters": self.filters,
            "tool_result": self.tool_result,
            "error": self.error,
            "retried": self.retried,
        }


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------


class Planner:
    """Converts a free-text chemistry question into a deterministic tool call.

    Parameters
    ----------
    provider:
        An initialised :class:`~backend.providers.base.BaseProvider`.
        This is the LLM used for intent detection and tool selection.
    database_path:
        Optional path to the DuckDB database.  Passed through to every
        tool call.  If ``None``, tools use the default database path.
    max_retries:
        How many times to retry after a JSON parse or validation failure.
        Default is ``1`` (one retry after the initial attempt).

    Example
    -------
    ::

        from backend.providers import get_provider
        from backend.planner import Planner

        planner = Planner(provider=get_provider())
        result = planner.plan("What catalysts are used in Buchwald-Hartwig reactions?")
        print(result.tool_result)
    """

    def __init__(
        self,
        provider: BaseProvider,
        *,
        database_path: str | Path | None = None,
        max_retries: int = 1,
    ) -> None:
        self._provider = provider
        self._database_path = database_path
        self._max_retries = max(0, int(max_retries))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan(self, question: str, model: str | None = None, timeout: float | None = None) -> PlannerResult:
        """Run the planner pipeline for a single user question.

        Parameters
        ----------
        question:
            Free-text question from the user.
        model:
            Optional override for the provider's default model.
        timeout:
            Timeout in seconds for the provider call.

        Returns
        -------
        PlannerResult
            Always returns a result — never raises.  Check
            ``result.success`` and ``result.error`` to detect failures.
        """
        question = question.strip()
        if not question:
            return PlannerResult(
                success=False,
                question=question,
                error="Question must not be empty.",
            )

        messages = self._build_messages(question)
        raw_response = ""

        for attempt in range(self._max_retries + 1):
            try:
                chat_response = self._provider.chat(messages, model=model, timeout=timeout)
                raw_response = chat_response.content
            except Exception as exc:  # noqa: BLE001
                return PlannerResult(
                    success=False,
                    question=question,
                    raw_llm_response=raw_response,
                    error=f"LLM provider error: {exc}",
                    retried=attempt > 0,
                )

            parse_result = self._parse_json(raw_response)
            if isinstance(parse_result, str):
                # parse_result is an error message
                if attempt < self._max_retries:
                    messages = self._build_retry_messages(
                        messages, raw_response, parse_result
                    )
                    continue
                return PlannerResult(
                    success=False,
                    question=question,
                    raw_llm_response=raw_response,
                    error=f"JSON parse error after {attempt + 1} attempt(s): {parse_result}",
                    retried=attempt > 0,
                )

            # parse_result is a parsed dict
            try:
                tool_name, filters = validate_planner_call(parse_result)
            except PlannerValidationError as exc:
                if attempt < self._max_retries:
                    messages = self._build_retry_messages(
                        messages, raw_response, str(exc)
                    )
                    continue
                return PlannerResult(
                    success=False,
                    question=question,
                    raw_llm_response=raw_response,
                    error=f"Validation error after {attempt + 1} attempt(s): {exc}",
                    retried=attempt > 0,
                )

            # Validated — dispatch
            return self._dispatch(
                question=question,
                tool_name=tool_name,
                filters=filters,
                raw_llm_response=raw_response,
                retried=attempt > 0,
            )

        # Should be unreachable
        return PlannerResult(  # pragma: no cover
            success=False,
            question=question,
            raw_llm_response=raw_response,
            error="Planner exhausted all retries without a valid response.",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_messages(self, question: str) -> list[Message]:
        return [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=question),
        ]

    @staticmethod
    def _build_retry_messages(
        original_messages: list[Message],
        bad_response: str,
        error: str,
    ) -> list[Message]:
        """Append the bad response and a correction instruction for the retry."""
        correction = (
            f"Your previous response was invalid: {error}\n"
            "Please respond with ONLY a valid JSON object matching the required format.\n"
            "Example: {\"tool\": \"search_reactions\", \"filters\": {\"reaction_type\": \"Suzuki\"}}"
        )
        return [
            *original_messages,
            Message(role="assistant", content=bad_response),
            Message(role="user", content=correction),
        ]

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any] | str:
        """Extract and parse the first JSON object from ``text``.

        Returns the parsed dict on success, or an error string on failure.

        The extraction uses three strategies in order:
        1. The entire response is JSON.
        2. Walk character-by-character to find the first balanced ``{...}``
           block (handles nested objects such as ``"filters": {}``).
        3. Return a descriptive error string.
        """
        text = text.strip()

        # Strategy 1: entire response is pure JSON.
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: brace-balanced scan for the first {...} block.
        start = text.find("{")
        if start != -1:
            depth = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(text[start:], start=start):
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\" and in_string:
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break  # malformed — fall through to error

        return f"Could not extract a JSON object from response: {text[:200]!r}"

    def _dispatch(
        self,
        *,
        question: str,
        tool_name: str,
        filters: dict[str, Any],
        raw_llm_response: str,
        retried: bool,
    ) -> PlannerResult:
        """Call the appropriate tool function and return a PlannerResult."""
        if tool_name == NO_TOOL:
            return PlannerResult(
                success=True,
                question=question,
                tool=NO_TOOL,
                filters={},
                tool_result=None,
                raw_llm_response=raw_llm_response,
                retried=retried,
            )

        tool_fn = _TOOL_DISPATCH[tool_name]

        # Inject database_path if the tool accepts it.
        call_kwargs: dict[str, Any] = dict(filters)
        if self._database_path is not None:
            call_kwargs["database_path"] = self._database_path

        try:
            result = tool_fn(**call_kwargs)
        except Exception as exc:  # noqa: BLE001
            return PlannerResult(
                success=False,
                question=question,
                tool=tool_name,
                filters=filters,
                raw_llm_response=raw_llm_response,
                error=f"Tool execution error: {exc}",
                retried=retried,
            )

        return PlannerResult(
            success=True,
            question=question,
            tool=tool_name,
            filters=filters,
            tool_result=result,
            raw_llm_response=raw_llm_response,
            retried=retried,
        )
