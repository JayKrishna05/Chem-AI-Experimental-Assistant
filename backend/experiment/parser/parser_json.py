import json
from typing import Any

from backend.experiment.models import CanonicalExperiment


def parse_json(data: str | dict[str, Any] | bytes, source: str = "json") -> list[CanonicalExperiment]:
    """Parse JSON string, bytes, or dict directly into a list of CanonicalExperiment."""
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    if isinstance(data, str):
        data = json.loads(data)
        
    if not isinstance(data, list):
        data = [data]
    
    experiments = []
    for item in data:
        experiments.append(CanonicalExperiment(
            source=source,
            reaction_type=item.get("reaction_type"),
            reactants=item.get("reactants", []),
            reagents=item.get("reagents", []),
            catalysts=item.get("catalysts", []),
            products=item.get("products", []),
            temperature_c=item.get("temperature_c"),
            yield_percent=item.get("yield_percent"),
            raw_data=item,
        ))
    
    return experiments
