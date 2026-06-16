"""Tests for the planner layer.

Structure
---------
Unit tests (always run — no LLM or DuckDB required):
  Schema validation:
    - Structural checks (missing keys, wrong types)
    - Known / unknown tool names
    - Filter key whitelist per tool
    - Filter type coercion (int, float, str)
    - Limit range validation
    - __none__ sentinel passes through
  JSON extraction:
    - Pure JSON response
    - JSON embedded in prose
    - JSON embedded with markdown fences
    - Completely unparseable response
  Planner dispatch (MockProvider):
    - Each of the 9 tools is dispatched correctly
    - __none__ returns success with no tool_result
    - JSON parse failure → retry → success
    - JSON parse failure → retry → failure (exhausted)
    - Validation failure → retry → success
    - Tool execution error is caught and returned
    - Empty question returns error immediately

Integration tests (skipped unless Ollama is reachable):
  - Live planner round-trip with a known chemistry question

Run with:
    python scripts/test_planner.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.planner import KNOWN_TOOLS, NO_TOOL, Planner, PlannerResult  # noqa: E402
from backend.planner.schema import (  # noqa: E402
    PlannerValidationError,
    validate_planner_call,
)
from backend.planner.planner import Planner as _PlannerCls  # noqa: E402
from backend.providers.base import BaseProvider, ChatResponse, Message  # noqa: E402


# ---------------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------------


@dataclass
class _Call:
    messages: list[Message]


class MockProvider(BaseProvider):
    """Provider whose responses are scripted by the test."""

    provider_name = "mock"

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.calls: list[_Call] = []

    def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
        self.calls.append(_Call(messages=list(messages)))
        if self._index >= len(self._responses):
            raise RuntimeError("MockProvider ran out of scripted responses")
        content = self._responses[self._index]
        self._index += 1
        return ChatResponse(content=content, model="mock", provider="mock")

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        raise NotImplementedError("MockProvider.generate not used in planner tests")


def _mock(responses: list[str]) -> MockProvider:
    return MockProvider(responses)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_json(text: str) -> dict[str, Any] | str:
    """Thin wrapper around Planner._parse_json for testing."""
    return _PlannerCls._parse_json(text)


def _planner(responses: list[str], *, max_retries: int = 1) -> Planner:
    """Build a Planner backed by a MockProvider."""
    return Planner(provider=MockProvider(responses), max_retries=max_retries)


# ---------------------------------------------------------------------------
# Tests: schema validation
# ---------------------------------------------------------------------------


def test_validate_missing_tool_key() -> None:
    try:
        validate_planner_call({"filters": {}})
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "tool" in str(exc)


def test_validate_missing_filters_key() -> None:
    try:
        validate_planner_call({"tool": "dataset_summary"})
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "filters" in str(exc)


def test_validate_not_a_dict() -> None:
    try:
        validate_planner_call("string")  # type: ignore[arg-type]
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError:
        pass


def test_validate_empty_tool_string() -> None:
    try:
        validate_planner_call({"tool": "  ", "filters": {}})
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError:
        pass


def test_validate_filters_not_a_dict() -> None:
    try:
        validate_planner_call({"tool": "dataset_summary", "filters": "bad"})
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "filters" in str(exc)


def test_validate_unknown_tool() -> None:
    try:
        validate_planner_call({"tool": "delete_all_data", "filters": {}})
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "delete_all_data" in str(exc)


def test_validate_none_sentinel_passes() -> None:
    tool, filters = validate_planner_call({"tool": NO_TOOL, "filters": {}})
    assert tool == NO_TOOL
    assert filters == {}


def test_validate_unknown_filter_key() -> None:
    try:
        validate_planner_call({
            "tool": "search_reactions",
            "filters": {"bad_key": "value"},
        })
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "bad_key" in str(exc)


def test_validate_dataset_summary_no_filters() -> None:
    tool, filters = validate_planner_call({"tool": "dataset_summary", "filters": {}})
    assert tool == "dataset_summary"
    assert filters == {}


def test_validate_dataset_summary_rejects_any_filter() -> None:
    try:
        validate_planner_call({
            "tool": "dataset_summary",
            "filters": {"reaction_type": "Suzuki"},
        })
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError:
        pass


def test_validate_int_coercion() -> None:
    """limit=10.0 (float from JSON) should be coerced to int 10."""
    tool, filters = validate_planner_call({
        "tool": "search_reactions",
        "filters": {"limit": 10.0},
    })
    assert isinstance(filters["limit"], int)
    assert filters["limit"] == 10


def test_validate_float_coercion() -> None:
    """temperature_min=80 (int from JSON) should be coerced to float 80.0."""
    tool, filters = validate_planner_call({
        "tool": "search_procedures",
        "filters": {"temperature_min": 80},
    })
    assert isinstance(filters["temperature_min"], float)
    assert filters["temperature_min"] == 80.0


def test_validate_limit_below_range() -> None:
    try:
        validate_planner_call({
            "tool": "search_reactions",
            "filters": {"limit": 0},
        })
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "limit" in str(exc)


def test_validate_limit_above_range() -> None:
    try:
        validate_planner_call({
            "tool": "search_reactions",
            "filters": {"limit": 101},
        })
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "limit" in str(exc)


def test_validate_string_filter_empty_rejected() -> None:
    try:
        validate_planner_call({
            "tool": "search_reactions",
            "filters": {"reaction_type": "   "},
        })
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError as exc:
        assert "reaction_type" in str(exc)


def test_validate_wrong_type_for_string_filter() -> None:
    try:
        validate_planner_call({
            "tool": "search_reactions",
            "filters": {"reaction_type": 123},
        })
        raise AssertionError("Expected PlannerValidationError")
    except PlannerValidationError:
        pass


def test_validate_known_tools_complete() -> None:
    """Every tool in KNOWN_TOOLS has a schema entry."""
    from backend.planner.schema import TOOL_FILTER_SCHEMAS
    assert KNOWN_TOOLS == frozenset(TOOL_FILTER_SCHEMAS)


# ---------------------------------------------------------------------------
# Tests: JSON extraction (_parse_json)
# ---------------------------------------------------------------------------


def test_parse_json_pure_json() -> None:
    raw = '{"tool": "dataset_summary", "filters": {}}'
    result = _parse_json(raw)
    assert isinstance(result, dict)
    assert result["tool"] == "dataset_summary"


def test_parse_json_json_in_prose() -> None:
    raw = 'Sure! Here is the answer: {"tool": "dataset_summary", "filters": {}} Hope that helps!'
    result = _parse_json(raw)
    assert isinstance(result, dict)
    assert result["tool"] == "dataset_summary"


def test_parse_json_with_markdown_fences() -> None:
    raw = '```json\n{"tool": "molecule_lookup", "filters": {"smiles": "Cl"}}\n```'
    result = _parse_json(raw)
    assert isinstance(result, dict)
    assert result["tool"] == "molecule_lookup"


def test_parse_json_completely_bad() -> None:
    raw = "I cannot answer that question."
    result = _parse_json(raw)
    assert isinstance(result, str)  # error message


def test_parse_json_empty_string() -> None:
    result = _parse_json("")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: Planner dispatch with MockProvider
# ---------------------------------------------------------------------------


def test_planner_search_reactions() -> None:
    p = _planner(['{"tool": "search_reactions", "filters": {"reaction_type": "Buchwald-Hartwig", "catalyst": "Pd"}}'])
    result = p.plan("Find Buchwald-Hartwig reactions with Pd catalyst")
    assert result.success is True
    assert result.tool == "search_reactions"
    assert result.filters["reaction_type"] == "Buchwald-Hartwig"
    assert result.filters["catalyst"] == "Pd"
    assert result.tool_result is not None
    assert result.tool_result["tool"] == "search_reactions"


def test_planner_search_procedures() -> None:
    p = _planner(['{"tool": "search_procedures", "filters": {"reaction_type": "Buchwald-Hartwig", "temperature_min": 80}}'])
    result = p.plan("Buchwald-Hartwig procedures above 80C")
    assert result.success is True
    assert result.tool == "search_procedures"
    assert result.filters["temperature_min"] == 80.0


def test_planner_molecule_lookup() -> None:
    p = _planner(['{"tool": "molecule_lookup", "filters": {"smiles": "Cl"}}'])
    result = p.plan("Look up molecule Cl")
    assert result.success is True
    assert result.tool == "molecule_lookup"
    assert result.tool_result["count"] >= 0


def test_planner_catalyst_statistics() -> None:
    p = _planner(['{"tool": "catalyst_statistics", "filters": {"reaction_type": "Buchwald-Hartwig", "limit": 5}}'])
    result = p.plan("Top catalysts for Buchwald-Hartwig")
    assert result.success is True
    assert result.tool == "catalyst_statistics"
    assert result.filters["limit"] == 5


def test_planner_yield_statistics() -> None:
    p = _planner(['{"tool": "yield_statistics", "filters": {}}'])
    result = p.plan("What is the average yield?")
    assert result.success is True
    assert result.tool == "yield_statistics"
    assert "statistics" in result.tool_result


def test_planner_temperature_statistics() -> None:
    p = _planner(['{"tool": "temperature_statistics", "filters": {"reaction_type": "Buchwald-Hartwig"}}'])
    result = p.plan("Temperature range for Buchwald-Hartwig")
    assert result.success is True
    assert result.tool == "temperature_statistics"
    assert "coverage" in result.tool_result


def test_planner_source_dataset_statistics() -> None:
    p = _planner(['{"tool": "source_dataset_statistics", "filters": {}}'])
    result = p.plan("Which datasets have the most reactions?")
    assert result.success is True
    assert result.tool == "source_dataset_statistics"
    assert isinstance(result.tool_result["results"], list)


def test_planner_reaction_type_statistics() -> None:
    p = _planner(['{"tool": "reaction_type_statistics", "filters": {"limit": 5}}'])
    result = p.plan("Most common reaction types")
    assert result.success is True
    assert result.tool == "reaction_type_statistics"
    assert result.filters["limit"] == 5


def test_planner_dataset_summary() -> None:
    p = _planner(['{"tool": "dataset_summary", "filters": {}}'])
    result = p.plan("Summarise the database")
    assert result.success is True
    assert result.tool == "dataset_summary"
    assert result.tool_result["counts"]["reaction_count"] == 2_376_120


def test_planner_no_tool_sentinel() -> None:
    p = _planner(['{"tool": "__none__", "filters": {}}'])
    result = p.plan("What is the capital of France?")
    assert result.success is True
    assert result.is_no_tool() is True
    assert result.tool_result is None


def test_planner_empty_question() -> None:
    p = _planner([])
    result = p.plan("   ")
    assert result.success is False
    assert result.error is not None
    assert len(p._provider.calls) == 0


def test_planner_provider_error() -> None:
    class FailProvider(BaseProvider):
        provider_name = "fail"

        def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
            raise RuntimeError("Network down")

        def generate(self, prompt: str, **kwargs: Any) -> Any:
            raise NotImplementedError

    p = Planner(provider=FailProvider())
    result = p.plan("Find reactions")
    assert result.success is False
    assert "Network down" in result.error


def test_planner_retry_on_bad_json_then_succeeds() -> None:
    """First response is prose, second is valid JSON — retry must kick in."""
    p = _planner([
        "Sorry, I don't understand.",
        '{"tool": "dataset_summary", "filters": {}}',
    ], max_retries=1)
    result = p.plan("Summarise the database")
    assert result.success is True
    assert result.tool == "dataset_summary"
    assert result.retried is True
    assert len(p._provider.calls) == 2  # type: ignore[attr-defined]


def test_planner_retry_exhausted_returns_error() -> None:
    """Both attempts return unparseable prose — must fail gracefully."""
    p = _planner([
        "I cannot help.",
        "Still cannot help.",
    ], max_retries=1)
    result = p.plan("Find reactions")
    assert result.success is False
    assert result.error is not None
    assert result.retried is True


def test_planner_retry_on_validation_error_then_succeeds() -> None:
    """First JSON has unknown tool, second is valid — retry triggers."""
    p = _planner([
        '{"tool": "delete_everything", "filters": {}}',
        '{"tool": "dataset_summary", "filters": {}}',
    ], max_retries=1)
    result = p.plan("Summarise the database")
    assert result.success is True
    assert result.tool == "dataset_summary"
    assert result.retried is True


def test_planner_no_retry_when_max_retries_zero() -> None:
    """With max_retries=0, a bad response immediately returns failure."""
    p = _planner(["not json at all"], max_retries=0)
    result = p.plan("Find reactions")
    assert result.success is False
    assert result.retried is False
    assert len(p._provider.calls) == 1  # type: ignore[attr-defined]


def test_planner_result_to_dict() -> None:
    p = _planner(['{"tool": "dataset_summary", "filters": {}}'])
    result = p.plan("Summarise")
    d = result.to_dict()
    assert "success" in d
    assert "tool" in d
    assert "filters" in d
    assert "tool_result" in d
    assert "error" in d


def test_planner_limit_coerced_in_dispatch() -> None:
    """Float limit from LLM JSON (10.0) is coerced to int 10 before tool call."""
    p = _planner(['{"tool": "search_reactions", "filters": {"limit": 5.0, "reaction_type": "Heck"}}'])
    result = p.plan("Heck reactions")
    assert result.success is True
    assert result.filters["limit"] == 5
    assert isinstance(result.filters["limit"], int)


def test_all_9_tools_in_dispatch_table() -> None:
    """Dispatch table must have an entry for every known tool."""
    from backend.planner.planner import _TOOL_DISPATCH
    assert KNOWN_TOOLS == frozenset(_TOOL_DISPATCH)


# ---------------------------------------------------------------------------
# Integration tests (skipped unless Ollama is reachable)
# ---------------------------------------------------------------------------


def _live_planner() -> Planner | None:
    """Return a live Planner if Ollama is reachable, else None."""
    try:
        from backend.providers.ollama_provider import OllamaProvider
        from backend.providers import load_config
        # Use a short timeout for the reachability probe.
        provider = OllamaProvider(config=load_config(), timeout=3)
        if not provider.is_reachable():
            return None
        return Planner(provider=provider)
    except Exception:  # noqa: BLE001
        return None


def _is_provider_error(result: PlannerResult) -> bool:
    """Return True if the failure was a provider connectivity problem."""
    if result.error is None:
        return False
    err = result.error.lower()
    return any(k in err for k in ("network error", "timed out", "connection", "ollama"))


def test_live_planner_dataset_summary() -> None:
    """Integration: live planner answers a question about the database."""
    p = _live_planner()
    if p is None:
        print("    SKIP  test_live_planner_dataset_summary (Ollama not reachable)")
        return

    result = p.plan("How many reactions are in the database?")
    if not result.success and _is_provider_error(result):
        print("    SKIP  test_live_planner_dataset_summary (Ollama timed out)")
        return
    assert result.success is True, f"Live planner failed: {result.error}"


def test_live_planner_catalyst_question() -> None:
    """Integration: live planner handles a catalyst question."""
    p = _live_planner()
    if p is None:
        print("    SKIP  test_live_planner_catalyst_question (Ollama not reachable)")
        return

    result = p.plan("Which catalysts are most common in Buchwald-Hartwig reactions?")
    if not result.success and _is_provider_error(result):
        print("    SKIP  test_live_planner_catalyst_question (Ollama timed out)")
        return
    assert result.success is True, f"Live planner failed: {result.error}"
    if not result.is_no_tool():
        assert result.tool_result is not None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def main() -> int:
    tests = [
        # Schema validation
        test_validate_missing_tool_key,
        test_validate_missing_filters_key,
        test_validate_not_a_dict,
        test_validate_empty_tool_string,
        test_validate_filters_not_a_dict,
        test_validate_unknown_tool,
        test_validate_none_sentinel_passes,
        test_validate_unknown_filter_key,
        test_validate_dataset_summary_no_filters,
        test_validate_dataset_summary_rejects_any_filter,
        test_validate_int_coercion,
        test_validate_float_coercion,
        test_validate_limit_below_range,
        test_validate_limit_above_range,
        test_validate_string_filter_empty_rejected,
        test_validate_wrong_type_for_string_filter,
        test_validate_known_tools_complete,
        # JSON extraction
        test_parse_json_pure_json,
        test_parse_json_json_in_prose,
        test_parse_json_with_markdown_fences,
        test_parse_json_completely_bad,
        test_parse_json_empty_string,
        # Planner dispatch
        test_planner_search_reactions,
        test_planner_search_procedures,
        test_planner_molecule_lookup,
        test_planner_catalyst_statistics,
        test_planner_yield_statistics,
        test_planner_temperature_statistics,
        test_planner_source_dataset_statistics,
        test_planner_reaction_type_statistics,
        test_planner_dataset_summary,
        test_planner_no_tool_sentinel,
        test_planner_empty_question,
        test_planner_provider_error,
        test_planner_retry_on_bad_json_then_succeeds,
        test_planner_retry_exhausted_returns_error,
        test_planner_retry_on_validation_error_then_succeeds,
        test_planner_no_retry_when_max_retries_zero,
        test_planner_result_to_dict,
        test_planner_limit_coerced_in_dispatch,
        test_all_9_tools_in_dispatch_table,
        # Live integration
        test_live_planner_dataset_summary,
        test_live_planner_catalyst_question,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {test.__name__}: {exc}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
