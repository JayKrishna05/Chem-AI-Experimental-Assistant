# ADR 0001: Use DuckDB for Analytics

**Date:** 2026-06-26
**Status:** Accepted

## Context
The platform needs to rapidly search and aggregate chemical reaction data across ~2.3 million reactions and ~1.8 million procedures. An OLAP (Online Analytical Processing) engine is required for high-performance grouped queries (e.g., yield statistics, temperature distributions, dataset counting) without incurring massive infrastructure costs or latency.

## Decision
We elected to use **DuckDB** as the primary in-process analytics engine.

## Alternatives Considered
- **SQLite**: Great for transactional workloads but exceptionally slow for columnar aggregations across millions of rows.
- **PostgreSQL**: Robust, but requires external service deployment, which complicates local development and the MVP footprint.
- **Pandas/Polars**: In-memory only; cannot efficiently hold or query the full dataset without massive RAM utilization.

## Consequences
- **Pros**: Lightning-fast OLAP queries, zero external dependencies (in-process engine), columnar vectorization, excellent JSON extraction capabilities.
- **Cons**: DuckDB struggles with concurrent multi-process writes. We are currently mitigating this via a read-only connection pool and will transition to PostgreSQL/SQLAlchemy when transactional persistence requires it.
