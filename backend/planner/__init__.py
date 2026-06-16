"""Planner package for the ORD Experimental Intelligence Assistant.

Public API
----------
- :class:`Planner` — main entry point
- :class:`PlannerResult` — return type of ``Planner.plan()``
- :data:`KNOWN_TOOLS` — frozenset of all registered tool names
- :exc:`PlannerValidationError` — raised when DSL validation fails

Usage::

    from backend.providers import get_provider
    from backend.planner import Planner

    planner = Planner(provider=get_provider())
    result = planner.plan("Which catalysts are most common in Buchwald-Hartwig?")

    if result.success and not result.is_no_tool():
        print(result.tool_result)
    elif result.is_no_tool():
        print("No tool matched the question.")
    else:
        print("Error:", result.error)
"""

from .planner import Planner, PlannerResult
from .schema import KNOWN_TOOLS, NO_TOOL, PlannerValidationError

__all__ = [
    "KNOWN_TOOLS",
    "NO_TOOL",
    "Planner",
    "PlannerResult",
    "PlannerValidationError",
]
