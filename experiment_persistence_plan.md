# Experiment Persistence Plan

## Overview
Currently, the Phase 5 upload pipeline is stateless. Uploaded files are parsed, validated, and compared in-memory, but they are never saved to disk or the database. This document details the persistence strategy for user experiments.

## Persistence Location
Persistence logic should reside in a new dedicated module:
- `backend/experiment/storage.py`

This module will contain functions like:
- `save_experiment(exp: CanonicalExperiment, user_id: str)`
- `list_user_experiments(user_id: str)`
- `delete_experiment(experiment_id: str)`

## Data Schema
Since `CanonicalExperiment` is already a strict Pydantic model, it translates naturally into a relational database schema or a document store.

### DuckDB / PostgreSQL Table Design
```sql
CREATE TABLE user_experiments (
    experiment_id UUID PRIMARY KEY,
    user_id UUID,
    source VARCHAR,
    created_at TIMESTAMP,
    schema_version VARCHAR,
    reaction_type VARCHAR,
    temperature_c FLOAT,
    yield_percent FLOAT,
    raw_text TEXT,
    raw_data JSONB
);

CREATE TABLE user_experiment_molecules (
    experiment_id UUID REFERENCES user_experiments(experiment_id),
    role VARCHAR, -- 'reactant', 'reagent', 'catalyst', 'product'
    name_or_smiles VARCHAR
);
```

## Readiness & PostgreSQL Migration
The current architecture is highly prepared for migration because:
1. **Decoupled Validation**: Validation logic ensures that the `CanonicalExperiment` is clean before it ever reaches a persistence layer.
2. **Schema Separation**: The `CanonicalExperiment` model acts as an internal DTO (Data Transfer Object). When SQLAlchemy is introduced, it will just map the Pydantic `CanonicalExperiment` to an SQLAlchemy `UserExperiment` declarative base.
3. **API Contracts**: The API layer (`backend/api/routes.py`) already manages the translation from HTTP requests to internal Python objects. Adding a `.save()` call before returning the `CompareExperimentResponse` is a trivial addition.
