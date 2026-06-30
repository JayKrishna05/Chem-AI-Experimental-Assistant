# Scientific Correctness Audit

## Overview
This document outlines areas in the current implementation where the AI Chemistry Engine may produce technically sound logic but scientifically misleading or incorrect insights. 

## 1. Similarity Search Vulnerability
*   **Location**: `backend/services/comparison_service.py`
*   **Issue**: The comparison service heuristically uses `exp.reactants[0]` and `exp.products[0]` to find "similar reactions."
*   **Scientific Impact**: Multi-component reactions, cross-couplings, and complex syntheses require precise matching of *all* critical reactants. Matching only the first index risks categorizing entirely different reaction classes as identical simply because they share a common starting material or solvent mistakenly listed as a reactant.

## 2. Reaction Type Filtering Trap
*   **Location**: `backend/tools/analytics_tools.py` (`top_yield_conditions`)
*   **Issue**: 99.97% of the ORD reactions in this database have `reaction_type = NULL`. The tool `top_yield_conditions` explicitly filters with `WHERE r.reaction_type IS NOT NULL`.
*   **Scientific Impact**: When comparing "optimal conditions" based on `reaction_type`, the system discards almost the entire dataset. A user uploading a "Buchwald-Hartwig" reaction is being compared against only the 0.03% of the dataset that had metadata explicitly labeling it, completely missing thousands of identical reactions in the remaining 99.97%.

## 3. Naive Yield Classifications
*   **Location**: `backend/services/comparison_service.py`
*   **Issue**: A user's yield is classified as an "Excellent Match" if the absolute difference is `<= 1.0` from the dataset average, and "Comparable" if `<= 5.0`.
*   **Scientific Impact**: A 1.0% yield difference on a 98% yield reaction is marginal, but a 1.0% difference on a 5% yield reaction is highly significant. Yield variance must account for standard deviation (`sample_stddev` provided by DuckDB) and reaction scale, rather than static percentage thresholds.

## 4. Temperature Profile Anomalies
*   **Location**: `backend/services/comparison_service.py`
*   **Issue**: Defines a temperature anomaly as `abs(diff) > 50` degrees from the clean statistics average.
*   **Scientific Impact**: 81% of the temperature records sit at 0°C (likely missing/default values). Averaging real temperatures with thousands of 0°C defaults skews the baseline downward, causing legitimate room-temperature or heated reactions to be falsely flagged as anomalous.

## 5. Ambiguous Reagents vs. Catalysts
*   **Location**: `backend/experiment/parser` and `backend/tools/`
*   **Issue**: ORD data often conflates catalysts, reagents, and solvents. The UI/LLM might report "No catalyst found" if a chemical (like Pd/C) was classified as a reagent by the original author.
*   **Scientific Impact**: False negatives in condition optimization.

## Conclusion
The foundational SQL metrics are computationally accurate, but their application in `comparison_service.py` lacks the rigorous chemical logic needed for production-grade analytical chemistry. 
