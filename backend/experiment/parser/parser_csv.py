import csv
from io import StringIO
from typing import Any

from backend.experiment.models import CanonicalExperiment


def parse_csv(data: str | bytes, source: str = "csv") -> list[CanonicalExperiment]:
    """Parse CSV text or bytes into a list of CanonicalExperiments using basic heuristics."""
    if isinstance(data, bytes):
        data = data.decode('utf-8')
        
    experiments = []
    reader = csv.DictReader(StringIO(data.strip()))
    
    for row in reader:
        # Standardize keys to lowercase for heuristic matching
        normalized_row = {k.lower().strip(): v.strip() for k, v in row.items() if k and v}
        
        # Heuristic extraction
        reaction_type = normalized_row.get("reaction_type") or normalized_row.get("type")
        temperature_c = normalized_row.get("temperature_c") or normalized_row.get("temp") or normalized_row.get("temperature")
        yield_percent = normalized_row.get("yield_percent") or normalized_row.get("yield") or normalized_row.get("yield %")
        
        # Parse list fields (comma separated)
        def _parse_list(key: str) -> list[str]:
            val = normalized_row.get(key, "")
            return [x.strip() for x in val.split(",")] if val else []

        reactants = _parse_list("reactants") or _parse_list("reactant")
        reagents = _parse_list("reagents") or _parse_list("reagent")
        catalysts = _parse_list("catalysts") or _parse_list("catalyst")
        products = _parse_list("products") or _parse_list("product")
        
        try:
            temp = float(temperature_c) if temperature_c else None
        except ValueError:
            temp = None
            
        try:
            yld = float(yield_percent) if yield_percent else None
        except (ValueError, TypeError):
            yld = None
            
        # Clean raw_data to ensure no None keys or values
        clean_row = {}
        for i, (k, v) in enumerate(row.items()):
            key = str(k).strip() if k is not None else f"column_{i}"
            clean_row[key] = str(v) if v is not None else ""
            
        exp = CanonicalExperiment(
            source=source,
            reaction_type=reaction_type,
            reactants=reactants,
            reagents=reagents,
            catalysts=catalysts,
            products=products,
            temperature_c=temp,
            yield_percent=yld,
            raw_data=clean_row,
        )
        experiments.append(exp)
        
    return experiments
