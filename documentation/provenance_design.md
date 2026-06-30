> **Historical Document**: This file was created during Phase 5 or 6 and is archived here for reference.

# Provenance & Explainability Design

## Objective
As the AI Chemistry Engine generates complex analytics (e.g., optimal conditions, temperature anomalies) based on user uploads, it is critical that scientists can trace *how* a conclusion was reached. A "black box" comparison is unacceptable for rigorous chemistry.

This document designs an `EvidenceBundle` provenance layer.

## The `EvidenceBundle` Model

Every comparison executed by `comparison_service.py` must eventually attach an `EvidenceBundle`.

```python
from pydantic import BaseModel
from typing import Any

class EvidenceBundle(BaseModel):
    # 1. Origin of data
    query_executed: str            # The exact logical intent or SQL executed
    source_datasets_queried: list[str]  # e.g. ["uspto", "ord-buchwald"]
    
    # 2. Statistical significance
    total_matching_rows: int       # Population size (e.g., 400 matching reactions)
    statistical_method: str        # e.g., "median", "clean_statistics mean"
    
    # 3. Assumptions & Caveats
    assumptions_made: list[str]    # e.g., ["Ignored reactions with yield > 100%"]
    confidence_rationale: str      # e.g., "High confidence: Sample size > 100 with low variance."
    
    # 4. Audit Trail
    raw_sample: list[dict[str, Any]] # 1-3 raw DB rows proving the assertion
```

## Integration Strategy

### 1. Comparison Engine Integration
Currently, `ComparisonResult` models (as proposed in `comparison_result_design.md`) contain fields like `best_avg_yield`. 
With this design, each insight (e.g., `YieldOptimization`) will have an `.evidence: EvidenceBundle` property.

```python
class YieldOptimization(BaseModel):
    reaction_type: str
    best_catalyst: str
    best_avg_yield: float
    is_suboptimal: bool
    evidence: EvidenceBundle  # The provenance
```

### 2. Formatter Integration
When the LLM Formatter streams the comparison report to the user, the Prompt will be updated to explicitly demand citations from the `EvidenceBundle`.

*Example Prompt Modification:*
> "When presenting an optimal condition or temperature anomaly, you MUST state the `total_matching_rows` and `assumptions_made` from the `evidence` block. For example: 'Using Pd/C yields 85% on average (based on 1,200 reactions, ignoring extreme outliers).'"

### 3. Frontend Integration
The Chat Interface can render standard text, but introduce a **"🔍 View Evidence"** accordion component below analytical claims. This allows scientists to click and see the exact SQL/parameters, sample sizes, and raw JSON rows that drove the LLM's conclusion, eliminating hallucination fears.
