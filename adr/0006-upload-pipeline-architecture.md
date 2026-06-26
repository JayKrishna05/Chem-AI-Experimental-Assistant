# ADR 0006: Upload Pipeline Architecture

**Date:** 2026-06-26
**Status:** Accepted

## Context
Phase 5 introduced the ability for users to upload their own experimental data (CSV, JSON, XLSX, Text) and compare it against the backend database. We required an architecture that prevents unstructured, noisy data from crashing the analytical engine while providing clear provenance and feedback to the user.

## Decision
We implemented a multi-stage deterministic deterministic pipeline:
`Upload -> File Identification -> Parser Dispatch -> Normalizer -> Validator -> Comparison Service`

1. **Parser Dispatch**: Identifies the MIME type and routes the binary `UploadFile` to the correct sub-parser.
2. **Parsers**: Independent modules that map raw data directly into a `CanonicalExperiment`. No database connection is allowed here.
3. **Normalizer**: Standardizes units, field aliases, and cleans up catalyst nomenclature (e.g., mapping "PALLADIUM" to "Pd") via DuckDB lookup tables.
4. **Validator**: Applies domain-specific constraints (e.g., yields cannot exceed 100%, temperatures cannot drop below absolute zero) and attaches a confidence score.

## Consequences
- **Pros**: Highly extensible. Adding a new format (e.g., a PDF parser or an ELN integration) merely requires writing a new parser that outputs a `CanonicalExperiment`. The rest of the pipeline handles the heavy lifting.
- **Cons**: The Normalizer stage is currently somewhat coupled to DuckDB for alias lookups, which may complicate testing and extraction in the future if a different database is used.
