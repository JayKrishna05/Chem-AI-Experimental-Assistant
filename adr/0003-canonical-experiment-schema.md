# ADR 0003: Canonical Experiment Schema

**Date:** 2026-06-26
**Status:** Accepted

## Context
When comparing user-uploaded experiments (which arrive in varying formats: CSV, JSON, raw text, and eventually PDF/ELN exports) against a backend database of 2.3M reactions, we need a standardized representation to ensure uniform validation and comparison logic.

## Decision
We introduced a **`CanonicalExperiment` Pydantic Model** as the central data contract for all uploaded experiments.

## Alternatives Considered
- **Direct Database Injection**: Too dangerous. Unvalidated schemas could corrupt the database.
- **Format-Specific Parsers feeding straight to Comparison**: Tight coupling between parsing logic and business logic leads to redundant code.

## Consequences
- **Pros**: The normalizer, validator, and comparison engine only ever see a `CanonicalExperiment`. This allows us to scale ingestion formats indefinitely (e.g., adding a PDF parser) without touching business logic.
- **Cons**: Every parser must map idiosyncratic data formats into this specific schema, requiring heuristic mapping logic (e.g., standardizing "yield %" vs "Yield" into `yield_percent`).
