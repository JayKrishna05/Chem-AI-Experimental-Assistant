> **Historical Document**: This file was created during Phase 5 and is archived here for reference.

# Upload Pipeline Robustness Review

## 1. Parser (`backend/experiment/parser.py`)
- **Current Responsibilities**: Consumes string/dict payloads and deterministically coerces them into `CanonicalExperiment` models. Provides specific entry points for JSON, CSV, and unstructured Text.
- **Hidden Assumptions**:
  - CSV parsing assumes commas separate values within list fields (e.g., `reactants: "A, B"`), which conflicts if IUPAC chemical names contain commas (e.g., `1,2-dichloroethane`).
  - Text parsing assumes regex `\d+ %` corresponds to the reaction yield. If the text mentions "catalyst loading of 5%", this will falsely parse as `yield_percent=5.0`.
  - Keys in CSV/JSON are expected to loosely match internal fields (e.g., `type`, `temp`, `yield`).
- **Failure Modes**:
  - `csv.DictReader` fails on malformed CSV strings (missing quotes, inconsistent column counts).
  - Passing integers/floats instead of strings in JSON arrays (e.g., `reactants: [1, 2]`) will crash the list comprehension `strip()` calls in normalization.
- **Opportunities for Modularity**:
  - Extract the fuzzy key-matching logic into a reusable `ColumnMapper` utility.
  - Offload list parsing into a dedicated function that can handle quoted commas to prevent breaking IUPAC names.

## 2. Normalizer (`backend/experiment/normalizer.py`)
- **Current Responsibilities**: Standardizes field names, units, and array data for consistency before DB lookup.
- **Hidden Assumptions**:
  - Capitalizes reaction types (e.g., `buchwald hartwig` -> `Buchwald-Hartwig`). It assumes the database uses Title Case, which might not be universally true.
  - Treats empty strings in lists as skippable.
- **Failure Modes**:
  - In-memory dictionary for catalyst aliases (`"palladium": "Pd"`) is incomplete and brittle. Unmapped aliases pass through silently and will fail DuckDB similarity searches.
- **Opportunities for Modularity**:
  - Convert normalization rules into a pipeline array, e.g., `[ReactionTypeNormalizer(), ArrayTrimNormalizer(), AliasNormalizer()]`. This allows dependency injection for a future Database-backed AliasNormalizer.

## 3. Validator (`backend/experiment/validator.py`)
- **Current Responsibilities**: Applies business logic constraints (bounds checking) and generates a non-fatal `ValidationResult`.
- **Hidden Assumptions**:
  - Assumes an experiment without `reactants` or `products` AND `yield` is entirely empty/failed.
  - Temperature bounds (-100°C to 300°C) are hardcoded heuristics based on standard organic chemistry, but may erroneously penalize high-temperature inorganic solid-state synthesis.
- **Failure Modes**:
  - Decrements `confidence_score` purely heuristically (-0.2, -0.1). If multiple warnings stack, confidence can drop to 0.0 even if the remaining data is highly valuable.
- **Opportunities for Modularity**:
  - Introduce rule-based validators. Each rule returns a discrete `ValidationWarning` object containing a severity level (WARNING, CRITICAL, INFO) rather than manipulating a global float.

## 4. Comparison Service (`backend/services/comparison_service.py`)
- **Current Responsibilities**: Consumes `ValidationResult` and orchestrates calls to existing DuckDB analytical tools. Returns comparative metrics.
- **Hidden Assumptions**:
  - Uses `reactants[0]` and `products[0]` for similarity search. This completely ignores multi-component reactions and will return misleading similarities for highly substituted scaffolds where the secondary reactant drives the novelty.
  - Assumes `temperature_statistics` returns a `clean_statistics` key. If the underlying tool contract changes, this throws a `KeyError` or silently returns None.
- **Failure Modes**:
  - Tight coupling to `analytics_tools.py` means any query modification or bug in the tool layer cascades directly into business logic failures here.
- **Opportunities for Modularity**:
  - Implement a Data Access Layer (DAL). The Comparison Service should not know about LLM tools; it should query `ExperimentRepository.get_average_temperature(reaction_type)`.
