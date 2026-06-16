"""JSON DSL schema validation for planner tool calls.

This module defines:

- The complete set of known tool names (``KNOWN_TOOLS``).
- Per-tool allowed filter keys and their expected Python types.
- ``validate_planner_call()`` — validates a raw parsed dict before any
  tool function is called.

All validation errors raise :exc:`PlannerValidationError` with a
human-readable message.  The planner catches this and returns it as an
error result without calling any tool.
"""

from __future__ import annotations

from typing import Any


class PlannerValidationError(ValueError):
    """Raised when a planner JSON DSL call fails schema validation."""


# ---------------------------------------------------------------------------
# No-op sentinel
# ---------------------------------------------------------------------------

NO_TOOL = "__none__"
"""Sentinel tool name the LLM outputs when no tool fits the question."""


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

# Maps each tool name to a dict of {filter_key: expected_type}.
# All filters are optional — this table controls what is *allowed*, not
# what is *required*.

_STR = str
_INT = int
_FLOAT = float

TOOL_FILTER_SCHEMAS: dict[str, dict[str, type]] = {
    "search_reactions": {
        "reaction_id": _STR,
        "reaction_type": _STR,
        "source_dataset": _STR,
        "source_dataset_id": _STR,
        "reactant": _STR,
        "reagent": _STR,
        "catalyst": _STR,
        "product": _STR,
        "limit": _INT,
    },
    "search_procedures": {
        "reaction_id": _STR,
        "reaction_type": _STR,
        "text": _STR,
        "temperature_min": _FLOAT,
        "temperature_max": _FLOAT,
        "yield_min": _FLOAT,
        "yield_max": _FLOAT,
        "limit": _INT,
    },
    "molecule_lookup": {
        "smiles": _STR,
        "query": _STR,
        "min_occurrences": _INT,
        "limit": _INT,
    },
    "catalyst_statistics": {
        "reaction_type": _STR,
        "source_dataset": _STR,
        "limit": _INT,
    },
    "yield_statistics": {
        "reaction_type": _STR,
        "source_dataset": _STR,
    },
    "temperature_statistics": {
        "reaction_type": _STR,
        "source_dataset": _STR,
    },
    "source_dataset_statistics": {
        "reaction_type": _STR,
        "limit": _INT,
    },
    "reaction_type_statistics": {
        "source_dataset": _STR,
        "limit": _INT,
    },
    "dataset_summary": {},
}

KNOWN_TOOLS: frozenset[str] = frozenset(TOOL_FILTER_SCHEMAS)
"""All tool names accepted by the planner (excludes ``__none__``)."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_planner_call(raw: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Validate and coerce a parsed planner JSON DSL call.

    Parameters
    ----------
    raw:
        A ``dict`` parsed from the LLM's JSON output.  Must contain
        ``"tool"`` and ``"filters"`` keys.

    Returns
    -------
    tuple[str, dict[str, Any]]
        ``(tool_name, coerced_filters)`` — ready to pass to the tool
        dispatch function.

    Raises
    ------
    PlannerValidationError
        If the call is structurally invalid, references an unknown tool,
        contains unknown filter keys, or has filter values of the wrong
        type.
    """
    # --- structural checks ------------------------------------------------
    if not isinstance(raw, dict):
        raise PlannerValidationError(
            f"Planner output must be a JSON object, got {type(raw).__name__}"
        )

    if "tool" not in raw:
        raise PlannerValidationError("Planner output is missing required key 'tool'")

    if "filters" not in raw:
        raise PlannerValidationError(
            "Planner output is missing required key 'filters'"
        )

    tool_name = raw["tool"]
    filters_raw = raw["filters"]

    if not isinstance(tool_name, str) or not tool_name.strip():
        raise PlannerValidationError(
            f"'tool' must be a non-empty string, got {tool_name!r}"
        )

    if not isinstance(filters_raw, dict):
        raise PlannerValidationError(
            f"'filters' must be a JSON object, got {type(filters_raw).__name__}"
        )

    # --- no-op sentinel ---------------------------------------------------
    if tool_name == NO_TOOL:
        return NO_TOOL, {}

    # --- tool name check --------------------------------------------------
    if tool_name not in KNOWN_TOOLS:
        known = ", ".join(sorted(KNOWN_TOOLS))
        raise PlannerValidationError(
            f"Unknown tool {tool_name!r}.  Known tools: {known}"
        )

    # --- filter key and type validation -----------------------------------
    schema = TOOL_FILTER_SCHEMAS[tool_name]
    coerced: dict[str, Any] = {}

    for key, value in filters_raw.items():
        if key not in schema:
            allowed = ", ".join(sorted(schema)) or "(none)"
            raise PlannerValidationError(
                f"Tool {tool_name!r} does not accept filter {key!r}.  "
                f"Allowed: {allowed}"
            )

        expected_type = schema[key]

        # Coerce numeric types leniently: the LLM may emit 80 as an int
        # when the schema expects float, or vice-versa.
        try:
            coerced_value = _coerce(key, value, expected_type)
        except (TypeError, ValueError) as exc:
            raise PlannerValidationError(
                f"Filter {key!r} for tool {tool_name!r}: {exc}"
            ) from exc

        coerced[key] = coerced_value

    # --- limit range check ------------------------------------------------
    if "limit" in coerced:
        limit = coerced["limit"]
        if not (1 <= limit <= 100):
            raise PlannerValidationError(
                f"'limit' must be between 1 and 100, got {limit}"
            )

    return tool_name, coerced


def _coerce(key: str, value: Any, expected: type) -> Any:
    """Coerce ``value`` to ``expected`` type with a helpful error."""
    if expected is _INT:
        if isinstance(value, bool):
            raise TypeError(f"Expected integer, got bool for key {key!r}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            coerced = int(value)
            if coerced != value:
                raise ValueError(
                    f"Expected integer, got non-integer float {value} for key {key!r}"
                )
            return coerced
        raise TypeError(
            f"Expected integer for key {key!r}, got {type(value).__name__} {value!r}"
        )

    if expected is _FLOAT:
        if isinstance(value, bool):
            raise TypeError(f"Expected number, got bool for key {key!r}")
        if isinstance(value, (int, float)):
            return float(value)
        raise TypeError(
            f"Expected number for key {key!r}, got {type(value).__name__} {value!r}"
        )

    if expected is _STR:
        if not isinstance(value, str):
            raise TypeError(
                f"Expected string for key {key!r}, got {type(value).__name__} {value!r}"
            )
        if not value.strip():
            raise ValueError(f"String filter {key!r} must not be empty or whitespace")
        return value

    raise TypeError(f"Unsupported schema type {expected} for key {key!r}")
