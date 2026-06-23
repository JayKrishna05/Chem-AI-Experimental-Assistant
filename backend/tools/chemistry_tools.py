"""Reusable DuckDB-backed chemistry retrieval tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db import connect_read_only
from backend.utils import sanitize_json


MAX_LIMIT = 100
DEFAULT_LIMIT = 10


def _normalize_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def _like_pattern(value: str) -> str:
    return f"%{value}%"


def _json_load(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value


def _append_like_filter(
    where_clauses: list[str],
    params: list[Any],
    column: str,
    value: str | None,
) -> None:
    if value:
        where_clauses.append(f"{column} ILIKE ?")
        params.append(_like_pattern(value))


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
    row_limit = _normalize_limit(limit)
    where_clauses: list[str] = []
    params: list[Any] = []

    _append_like_filter(where_clauses, params, "reaction_id", reaction_id)
    _append_like_filter(where_clauses, params, "reaction_type", reaction_type)
    _append_like_filter(where_clauses, params, "source_dataset", source_dataset)
    _append_like_filter(where_clauses, params, "source_dataset_id", source_dataset_id)
    _append_like_filter(where_clauses, params, "CAST(reactants_json AS VARCHAR)", reactant)
    _append_like_filter(where_clauses, params, "CAST(reagents_json AS VARCHAR)", reagent)
    _append_like_filter(where_clauses, params, "CAST(catalysts_json AS VARCHAR)", catalyst)
    _append_like_filter(where_clauses, params, "CAST(products_json AS VARCHAR)", product)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
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

    returned_rows = len(results)
    return sanitize_json({
        "tool": "search_reactions",
        "filters": {
            "reaction_id": reaction_id,
            "reaction_type": reaction_type,
            "source_dataset": source_dataset,
            "source_dataset_id": source_dataset_id,
            "reactant": reactant,
            "reagent": reagent,
            "catalyst": catalyst,
            "product": product,
        },
        "limit": row_limit,
        "returned_rows": returned_rows,
        "total_matching_rows": total_matching_rows,
        "truncated": total_matching_rows > returned_rows,
        "results": results,
    })



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
    row_limit = _normalize_limit(limit)
    where_clauses: list[str] = []
    params: list[Any] = []

    _append_like_filter(where_clauses, params, "reaction_id", reaction_id)
    _append_like_filter(where_clauses, params, "reaction_type", reaction_type)
    _append_like_filter(where_clauses, params, "procedure_text", text)

    if temperature_min is not None:
        where_clauses.append("temperature_c >= ?")
        params.append(float(temperature_min))
    if temperature_max is not None:
        where_clauses.append("temperature_c <= ?")
        params.append(float(temperature_max))
    if yield_min is not None:
        where_clauses.append("yield_percent >= ?")
        params.append(float(yield_min))
    if yield_max is not None:
        where_clauses.append("yield_percent <= ?")
        params.append(float(yield_max))

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
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

    returned_rows = len(results)
    return sanitize_json({
        "tool": "search_procedures",
        "filters": {
            "reaction_id": reaction_id,
            "reaction_type": reaction_type,
            "text": text,
            "temperature_min": temperature_min,
            "temperature_max": temperature_max,
            "yield_min": yield_min,
            "yield_max": yield_max,
        },
        "limit": row_limit,
        "returned_rows": returned_rows,
        "total_matching_rows": total_matching_rows,
        "truncated": total_matching_rows > returned_rows,
        "results": results,
    })



def molecule_lookup(
    *,
    smiles: str | None = None,
    query: str | None = None,
    min_occurrences: int | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Look up molecules by exact SMILES or substring query."""
    row_limit = _normalize_limit(limit)
    where_clauses: list[str] = []
    params: list[Any] = []

    if smiles:
        where_clauses.append("smiles = ?")
        params.append(smiles)
    if query:
        where_clauses.append("smiles ILIKE ?")
        params.append(_like_pattern(query))
    if min_occurrences is not None:
        where_clauses.append("occurrences >= ?")
        params.append(int(min_occurrences))

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
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

    returned_rows = len(results)
    return sanitize_json({
        "tool": "molecule_lookup",
        "filters": {
            "smiles": smiles,
            "query": query,
            "min_occurrences": min_occurrences,
        },
        "limit": row_limit,
        "returned_rows": returned_rows,
        "total_matching_rows": total_matching_rows,
        "truncated": total_matching_rows > returned_rows,
        "results": results,
    })
