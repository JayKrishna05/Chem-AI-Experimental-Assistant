# Typed Comparison Result Design

## Overview
Currently, `backend/services/comparison_service.py` returns an anonymous dictionary containing arbitrary nested dictionaries (e.g., `comparisons["similar_reactions"]`, `comparisons["temperature_profile"]`). This design proposal outlines a migration to a strongly-typed Pydantic model (`ComparisonResult`).

## Proposed Fields

```python
from pydantic import BaseModel, Field

class TemperatureAnomaly(BaseModel):
    user_temperature: float
    db_average_temperature: float
    difference: float
    is_anomalous: bool

class YieldOptimization(BaseModel):
    reaction_type: str
    best_catalyst: str | None
    best_avg_yield: float | None
    user_yield: float | None
    is_suboptimal: bool

class SimilarReactionMatch(BaseModel):
    reaction_id: str
    reaction_type: str | None

class SimilaritySearch(BaseModel):
    total_matching: int
    top_matches: list[SimilarReactionMatch]

class ComparisonResult(BaseModel):
    experiment_id: str
    is_valid: bool
    warnings: list[str] = Field(default_factory=list)
    confidence_score: float
    
    # Specific Domain Comparisons
    temperature_profile: TemperatureAnomaly | None = None
    optimal_conditions: YieldOptimization | None = None
    similar_reactions: SimilaritySearch | None = None
```

## Rationale
- **IDE Autocomplete & Introspection**: Downstream services (and the API layer) can inspect the `ComparisonResult` object natively without guessing string keys.
- **Documentation**: FastAPI automatically generates an OpenAPI schema for this model, self-documenting the exact shape of a comparison output.
- **Safety**: Prevents `KeyError` exceptions if the frontend expects `temperature_profile` but the service omitted it because the database returned no data.

## Migration Effort
- **Low Effort**: The comparison logic already generates these precise variables. We simply replace the `report["comparisons"]["key"] = {...}` assignments with Pydantic class instantiations.
- **Refactor Impact**: `routes.py` will update its `CompareExperimentResponse` to return `comparisons: list[ComparisonResult]` instead of `list[Any]`.

## Expected Downstream Benefits
- The frontend Next.js application can generate TypeScript interfaces directly from this Pydantic schema, guaranteeing type safety end-to-end.
- The Formatter LLM can be given a strict schema prompt if we later want it to write customized prose based on the `ComparisonResult`.
