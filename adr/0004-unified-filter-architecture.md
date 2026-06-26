# ADR 0004: Unified Filter Architecture

**Date:** 2026-06-26
**Status:** Accepted

## Context
Previously, analytical tools in the platform (`catalyst_statistics`, `yield_statistics`, etc.) constructed their SQL `WHERE` clauses independently. This led to inconsistent filter support (e.g., some tools dropped temperature boundaries entirely) and created a high risk of the LLM receiving data that answered a fundamentally different question than the user asked.

## Decision
We extracted all SQL filtering logic into a central infrastructure component (`backend/tools/filters.py`) featuring a `FilterBuilder`. Every tool now delegates its parameter ingestion to this unified builder.

## Alternatives Considered
- **SQLAlchemy/ORM Filtering**: We elected to stay with raw SQL strings for DuckDB performance and transparency, rather than imposing a heavy ORM layer on a read-only analytics workload.

## Consequences
- **Pros**: Guaranteed consistency across all endpoints. If a filter is applied, it works universally. The risk of silently dropped filters is eradicated.
- **Cons**: Tool functions are now tightly coupled to the `FilterBuilder`. Refactoring the schema requires updating this central module.
