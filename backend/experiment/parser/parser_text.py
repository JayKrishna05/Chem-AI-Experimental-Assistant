import re
from typing import Any

from backend.experiment.models import CanonicalExperiment


def parse_text(data: str | bytes, source: str = "text") -> list[CanonicalExperiment]:
    """Parse unstructured text using deterministic regex/heuristics."""
    if isinstance(data, bytes):
        data = data.decode('utf-8')
        
    temperature_c = None
    yield_percent = None
    
    # Very basic regex heuristics
    temp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:°C|deg C|Celsius|C\b)', data, re.IGNORECASE)
    if temp_match:
        temperature_c = float(temp_match.group(1))
        
    yield_match = re.search(r'(\d+(?:\.\d+)?)\s*%', data)
    if yield_match:
        yield_percent = float(yield_match.group(1))
        
    # Return as list of 1 experiment to match other parsers
    return [CanonicalExperiment(
        source=source,
        temperature_c=temperature_c,
        yield_percent=yield_percent,
        raw_text=data,
    )]
