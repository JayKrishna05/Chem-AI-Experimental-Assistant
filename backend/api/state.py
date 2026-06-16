"""Global API state."""

active_models: dict[str, str | float | None] = {
    "planner_model": "gemma4:12b-it-qat",
    "formatter_model": "gemma4:12b-it-qat",
    "formatter_timeout": 59.0,
}
