"""Reusable filter definitions and SQL helpers for ORD chemistry tools."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable

def _like_pattern(value: str) -> str:
    return f"%{value}%"

@dataclass
class CommonFilters:
    """Common filters supported across tools. Tools can pick and choose which they support."""
    reaction_id: str | None = None
    reaction_type: str | None = None
    source_dataset: str | None = None
    source_dataset_id: str | None = None
    reactant: str | None = None
    reagent: str | None = None
    catalyst: str | None = None
    product: str | None = None
    text: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    yield_min: float | None = None
    yield_max: float | None = None
    smiles: str | None = None
    query: str | None = None
    min_occurrences: int | None = None
    group_by: str | None = None
    sort_by: str | None = None

def build_filters(
    filters: CommonFilters,
    reaction_alias: str = "r",
    procedure_alias: str = "p",
    molecule_alias: str = "m"
) -> tuple[list[str], list[Any]]:
    """Build WHERE clauses and parameters from CommonFilters.
    
    Aliases default to 'r' for reactions, 'p' for procedures, 'm' for molecules.
    Tools should ensure tables are joined if using mixed filters.
    """
    clauses: list[str] = []
    params: list[Any] = []

    def _add_like(column: str, value: str | None):
        if value:
            clauses.append(f"{column} ILIKE ?")
            params.append(_like_pattern(value))

    def _add_exact(column: str, value: str | None):
        if value:
            clauses.append(f"{column} = ?")
            params.append(value)

    # Reaction filters
    _add_like(f"{reaction_alias}.reaction_id", filters.reaction_id)
    _add_like(f"{reaction_alias}.reaction_type", filters.reaction_type)
    _add_like(f"{reaction_alias}.source_dataset", filters.source_dataset)
    _add_like(f"{reaction_alias}.source_dataset_id", filters.source_dataset_id)
    _add_like(f"CAST({reaction_alias}.reactants_json AS VARCHAR)", filters.reactant)
    _add_like(f"CAST({reaction_alias}.reagents_json AS VARCHAR)", filters.reagent)
    _add_like(f"CAST({reaction_alias}.catalysts_json AS VARCHAR)", filters.catalyst)
    _add_like(f"CAST({reaction_alias}.products_json AS VARCHAR)", filters.product)

    # Procedure filters
    _add_like(f"{procedure_alias}.procedure_text", filters.text)
    if filters.temperature_min is not None:
        clauses.append(f"{procedure_alias}.temperature_c >= ?")
        params.append(filters.temperature_min)
    if filters.temperature_max is not None:
        clauses.append(f"{procedure_alias}.temperature_c <= ?")
        params.append(filters.temperature_max)
    if filters.yield_min is not None:
        clauses.append(f"{procedure_alias}.yield_percent >= ?")
        params.append(filters.yield_min)
    if filters.yield_max is not None:
        clauses.append(f"{procedure_alias}.yield_percent <= ?")
        params.append(filters.yield_max)

    # Molecule filters
    _add_exact(f"{molecule_alias}.smiles", filters.smiles)
    _add_like(f"{molecule_alias}.smiles", filters.query)
    if filters.min_occurrences is not None:
        clauses.append(f"{molecule_alias}.occurrences >= ?")
        params.append(filters.min_occurrences)

    return clauses, params

def build_where_sql(clauses: list[str]) -> str:
    """Build the WHERE SQL string from a list of clauses."""
    return f"WHERE {' AND '.join(clauses)}" if clauses else ""

def build_limit(limit: int | None, max_limit: int = 100) -> int:
    """Normalize row limits."""
    if limit is None:
        return 10
    return max(1, min(int(limit), max_limit))

def format_tool_response(
    *,
    tool_name: str,
    applied_filters: dict[str, Any],
    results: list[Any] | dict[str, Any],
    total_matching_rows: int,
    limit: int | None = None,
    assumptions: list[str] | None = None,
    start_time: float,
) -> dict[str, Any]:
    """Standardize tool response structure to guarantee backward compatibility 
    while adding new metadata fields."""
    
    execution_time_ms = round((time.time() - start_time) * 1000, 2)
    
    is_list = isinstance(results, list)
    returned_rows = len(results) if is_list else 1
    truncated = bool(is_list and limit and total_matching_rows > limit)

    response = {
        "tool": tool_name,
        "contract_version": "1.0",
        "execution_time_ms": execution_time_ms,
        "applied_filters": applied_filters,  # new standard metadata
        "filters": applied_filters,          # backward compatible
        "limit": limit or 0,
        "count": returned_rows,        # backward compatible (some tools used this as total_matching_rows, wait actually they used len(results))
        "returned_rows": returned_rows,
        "total_matching_rows": total_matching_rows,
        "truncated": truncated,
        "assumptions": assumptions or [],
        "results": results if is_list else [results], # Always a list of results if possible? Wait, some endpoints return dict inline.
    }
    
    # If the tool was returning a dict natively (like dataset_summary), we just merge it, 
    # but the instructions said "Standardize list-returning tools". 
    # Let's keep results under the "results" key or merge it.
    if not is_list:
        for k, v in results.items():
            if k not in response:
                response[k] = v
        # Remove 'results' key if we just flattened a dict? 
        # Actually, let's keep things consistent with the old schema which expected certain nested keys.
        # But wait, dataset_summary returns `{"tool": "...", "counts": {...}, "reaction_coverage": {...}}`.
        # To not break it, if not a list, we merge. 
        del response["results"]

    return response
