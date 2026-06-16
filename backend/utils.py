"""Utility functions for backend."""

import math
from typing import Any

def sanitize_json(obj: Any) -> Any:
    """Recursively replace NaN, Infinity, and -Infinity with None for valid JSON."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_json(v) for v in obj)
    return obj
