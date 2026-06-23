"""Global API state.

``active_models`` is a mutable dict that acts as the runtime configuration
for both model and provider selection.  It is read at request time by
``chat_routes.py`` and ``stream.py``.

Keys
----
planner_provider   : str   — provider name for the planner (e.g. "ollama", "groq")
planner_model      : str   — model name passed to the planner provider
planner_timeout    : float — HTTP timeout in seconds for planner calls

formatter_provider : str   — provider name for the formatter (may differ from planner)
formatter_model    : str   — model name passed to the formatter provider
formatter_timeout  : float — HTTP timeout in seconds for formatter calls
"""

active_models: dict[str, str | float | None] = {
    "planner_provider": "ollama",
    "planner_model": "gemma4:12b-it-qat",
    "planner_timeout": 59.0,
    "formatter_provider": "ollama",
    "formatter_model": "gemma4:12b-it-qat",
    "formatter_timeout": 59.0,
}

