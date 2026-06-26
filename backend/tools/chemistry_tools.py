"""Reusable DuckDB-backed chemistry retrieval tools."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .db import connect_read_only
from backend.utils import sanitize_json
from .filters import CommonFilters, build_filters, build_where_sql, build_limit, format_tool_response

MAX_LIMIT = 100
DEFAULT_LIMIT = 10


def _json_load(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value

def _execute_structured_query(
    database_path: str | Path | None,
    sql: str,
    params: list[Any],
) -> tuple[list[str], list[tuple[Any, ...]]]:
    with connect_read_only(database_path) as con:
        cursor = con.execute(sql, params)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
    return columns, rows

def _execute_count_query(
    database_path: str | Path | None,
    sql: str,
    params: list[Any],
) -> int:
    with connect_read_only(database_path) as con:
        cursor = con.execute(sql, params)
        row = cursor.fetchone()
    return row[0] if row else 0


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
    where_clauses, params = build_filters(filters_model, reaction_alias="reactions")
    where_sql = build_where_sql(where_clauses)
    
    count_sql = f"SELECT COUNT(*) FROM reactions {where_sql}"
    total_matching_rows = _execute_count_query(database_path, count_sql, params)

    params.append(row_limit)
    sql = f"""
        SELECT
            reaction_id,
            reaction_type,
            source_dataset,
            source_dataset_id,
            reactants_json,
            reagents_json,
            catalysts_json,
            products_json,
            conditions_json
        FROM reactions
        {where_sql}
        ORDER BY reaction_id
        LIMIT ?
    """
    columns, rows = _execute_structured_query(database_path, sql, params)
    json_columns = {
        "reactants_json",
        "reagents_json",
        "catalysts_json",
        "products_json",
        "conditions_json",
    }
    results = []
    for row in rows:
        item = dict(zip(columns, row, strict=True))
        for column in json_columns:
            item[column] = _json_load(item[column])
        results.append(item)

    return sanitize_json(format_tool_response(
        tool_name="search_reactions",
        applied_filters=applied_filters_dict,
        results=results,
        total_matching_rows=total_matching_rows,
        limit=row_limit,
        start_time=start_time,
    ))


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
    where_clauses, params = build_filters(
        filters_model, 
        reaction_alias="procedures", 
        procedure_alias="procedures"
    )
    where_sql = build_where_sql(where_clauses)
    
    count_sql = f"SELECT COUNT(*) FROM procedures {where_sql}"
    total_matching_rows = _execute_count_query(database_path, count_sql, params)

    params.append(row_limit)
    sql = f"""
        SELECT
            reaction_id,
            reaction_type,
            temperature_c,
            yield_percent,
            procedure_text
        FROM procedures
        {where_sql}
        ORDER BY reaction_id
        LIMIT ?
    """
    columns, rows = _execute_structured_query(database_path, sql, params)
    results = [dict(zip(columns, row, strict=True)) for row in rows]

    return sanitize_json(format_tool_response(
        tool_name="search_procedures",
        applied_filters=applied_filters_dict,
        results=results,
        total_matching_rows=total_matching_rows,
        limit=row_limit,
        start_time=start_time,
    ))


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
    where_clauses, params = build_filters(filters_model, molecule_alias="molecules")
    where_sql = build_where_sql(where_clauses)
    
    count_sql = f"SELECT COUNT(*) FROM molecules {where_sql}"
    total_matching_rows = _execute_count_query(database_path, count_sql, params)

    params.append(row_limit)
    sql = f"""
        SELECT smiles, occurrences
        FROM molecules
        {where_sql}
        ORDER BY occurrences DESC, smiles
        LIMIT ?
    """
    columns, rows = _execute_structured_query(database_path, sql, params)
    results = [dict(zip(columns, row, strict=True)) for row in rows]

    return sanitize_json(format_tool_response(
        tool_name="molecule_lookup",
        applied_filters=applied_filters_dict,
        results=results,
        total_matching_rows=total_matching_rows,
        limit=row_limit,
        start_time=start_time,
    ))
