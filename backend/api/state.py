"""Global API state."""

active_models: dict[str, str | None] = {
    "planner_model": None,
    "formatter_model": None,
}
