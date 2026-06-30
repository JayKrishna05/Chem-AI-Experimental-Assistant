"""Reusable DuckDB-backed chemistry retrieval tools.
Now acts as a thin formatting layer over ReactionRepository and ProcedureRepository.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from backend.tools.filters import CommonFilters, build_limit, format_tool_response
from backend.database.repositories.reaction_repository import ReactionRepository
from backend.database.repositories.procedure_repository import ProcedureRepository

MAX_LIMIT = 100
DEFAULT_LIMIT = 10

def search_reactions(
    *,
    reaction_id: str | None = None,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    source_dataset_id: str | None = None,
    reactant: str | None = None,
    reagent: str | None = None,
    catalyst: str | None = None,
    product: str | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Search ORD reactions with scalar and chemistry JSON filters."""
    start_time = time.time()
    row_limit = build_limit(limit, MAX_LIMIT)
    
    applied_filters_dict = {
        "reaction_id": reaction_id,
        "reaction_type": reaction_type,
        "source_dataset": source_dataset,
        "source_dataset_id": source_dataset_id,
        "reactant": reactant,
        "reagent": reagent,
        "catalyst": catalyst,
        "product": product,
    }
    
    filters_model = CommonFilters(**applied_filters_dict)
    
    repo = ReactionRepository(database_path)
    results, total_rows = repo.search_reactions(filters_model, row_limit)

    return format_tool_response(
        tool_name="search_reactions",
        applied_filters=applied_filters_dict,
        results=results,
        total_matching_rows=total_rows,
        limit=row_limit,
        start_time=start_time,
    )


def search_procedures(
    *,
    reaction_id: str | None = None,
    reaction_type: str | None = None,
    text: str | None = None,
    temperature_min: float | None = None,
    temperature_max: float | None = None,
    yield_min: float | None = None,
    yield_max: float | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Search experimental procedures with text and numeric filters."""
    start_time = time.time()
    row_limit = build_limit(limit, MAX_LIMIT)
    
    applied_filters_dict = {
        "reaction_id": reaction_id,
        "reaction_type": reaction_type,
        "text": text,
        "temperature_min": temperature_min,
        "temperature_max": temperature_max,
        "yield_min": yield_min,
        "yield_max": yield_max,
    }
    
    filters_model = CommonFilters(**applied_filters_dict)
    
    repo = ProcedureRepository(database_path)
    results, total_rows = repo.search_procedures(filters_model, row_limit)

    return format_tool_response(
        tool_name="search_procedures",
        applied_filters=applied_filters_dict,
        results=results,
        total_matching_rows=total_rows,
        limit=row_limit,
        start_time=start_time,
    )


def molecule_lookup(
    *,
    smiles: str | None = None,
    query: str | None = None,
    min_occurrences: int | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Look up molecules by exact SMILES or substring query."""
    start_time = time.time()
    row_limit = build_limit(limit, MAX_LIMIT)
    
    applied_filters_dict = {
        "smiles": smiles,
        "query": query,
        "min_occurrences": min_occurrences,
    }
    
    filters_model = CommonFilters(**applied_filters_dict)
    
    repo = ReactionRepository(database_path)
    results, total_rows = repo.molecule_lookup(filters_model, row_limit)

    return format_tool_response(
        tool_name="molecule_lookup",
        applied_filters=applied_filters_dict,
        results=results,
        total_matching_rows=total_rows,
        limit=row_limit,
        start_time=start_time,
    )
