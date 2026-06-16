"""Tests for JSON sanitization utility."""

import json
import math
from backend.utils import sanitize_json

def test_sanitize_json_handles_nan_and_inf():
    test_data = {
        "normal_string": "hello",
        "normal_int": 42,
        "normal_float": 3.14,
        "nan_value": float("nan"),
        "pos_inf": float("inf"),
        "neg_inf": float("-inf"),
        "nested_dict": {
            "inner_nan": float("nan"),
            "inner_list": [1.0, float("inf"), float("-inf"), "test"]
        },
        "nested_tuple": (float("nan"), 2.0)
    }

    sanitized = sanitize_json(test_data)
    
    # Assert values are replaced with None
    assert sanitized["nan_value"] is None
    assert sanitized["pos_inf"] is None
    assert sanitized["neg_inf"] is None
    
    assert sanitized["nested_dict"]["inner_nan"] is None
    assert sanitized["nested_dict"]["inner_list"][1] is None
    assert sanitized["nested_dict"]["inner_list"][2] is None
    
    assert sanitized["nested_tuple"][0] is None
    
    # Assert valid JSON serialization
    try:
        json_str = json.dumps(sanitized)
        # Verify no NaN or Infinity is in the string
        assert "NaN" not in json_str
        assert "Infinity" not in json_str
        # Double check parsing works
        parsed = json.loads(json_str)
        assert parsed["nan_value"] is None
    except Exception as e:
        assert False, f"JSON serialization failed after sanitization: {e}"

if __name__ == "__main__":
    test_sanitize_json_handles_nan_and_inf()
    print("All JSON sanitization tests passed!")
