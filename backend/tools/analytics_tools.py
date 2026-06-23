"""DuckDB-backed analytics tools for ORD chemistry and procedures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .chemistry_tools import DEFAULT_LIMIT, _like_pattern, _normalize_limit
from .db import connect_read_only


from backend.utils import sanitize_json

def _fetch_one(
    database_path: str | Path | None,
    sql: str,
    params: list[Any] | None = None,
) -> dict[str, Any]:
    with connect_read_only(database_path) as con:
        cursor = con.execute(sql, params or [])
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
    if row:
        return sanitize_json(dict(zip(columns, row, strict=True)))
    return {}


def _fetch_all(
    database_path: str | Path | None,
    sql: str,
    params: list[Any] | None = None,
) -> list[dict[str, Any]]:
    with connect_read_only(database_path) as con:
        cursor = con.execute(sql, params or [])
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
    return [sanitize_json(dict(zip(columns, row, strict=True))) for row in rows]


def _reaction_filters(
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    alias: str = "r",
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if reaction_type:
        clauses.append(f"{alias}.reaction_type ILIKE ?")
        params.append(_like_pattern(reaction_type))
    if source_dataset:
        clauses.append(f"{alias}.source_dataset ILIKE ?")
        params.append(_like_pattern(source_dataset))
    return clauses, params


def _where_sql(clauses: list[str]) -> str:
    return f"WHERE {' AND '.join(clauses)}" if clauses else ""


def _numeric_statistics(
    *,
    tool: str,
    table_expression: str,
    value_column: str,
    value_name: str,
    where_clauses: list[str],
    params: list[Any],
    filters: dict[str, Any],
    assumptions: list[str],
    database_path: str | Path | None,
) -> dict[str, Any]:
    valid_clause = f"{value_column} IS NOT NULL AND isfinite({value_column})"
    where_sql = _where_sql([*where_clauses, valid_clause])
    all_where_sql = _where_sql(where_clauses)

    summary = _fetch_one(
        database_path,
        f"""
        SELECT
            COUNT(*) AS count,
            AVG({value_column}) AS average,
            MEDIAN({value_column}) AS median,
            MIN({value_column}) AS minimum,
            MAX({value_column}) AS maximum,
            STDDEV_SAMP({value_column}) AS sample_stddev,
            quantile_cont({value_column}, 0.25) AS p25,
            quantile_cont({value_column}, 0.75) AS p75
        FROM {table_expression}
        {where_sql}
        """,
        params,
    )
    coverage = _fetch_one(
        database_path,
        f"""
        SELECT
            COUNT(*) AS total_records,
            COUNT({value_column}) AS records_with_value,
            COALESCE(SUM(
                CASE
                    WHEN {value_column} IS NOT NULL AND isfinite({value_column})
                    THEN 1
                    ELSE 0
                END
            ), 0) AS records_with_finite_value
        FROM {table_expression}
        {all_where_sql}
        """,
        params,
    )

    return {
        "tool": tool,
        "filters": filters,
        "metric": value_name,
        "coverage": coverage,
        "statistics": summary,
        "assumptions": assumptions,
    }


def catalyst_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Rank catalyst entries by occurrence and distinct reaction coverage."""
    row_limit = _normalize_limit(limit)
    where_clauses, params = _reaction_filters(reaction_type, source_dataset)
    where_clauses.append("json_array_length(r.catalysts_json) > 0")
    where_sql = _where_sql(where_clauses)
    params.append(row_limit)

    results = _fetch_all(
        database_path,
        f"""
        SELECT
            COALESCE(json_extract_string(c.value, '$.smiles'), '') AS catalyst_smiles,
            COALESCE(json_extract_string(c.value, '$.name'), '') AS catalyst_name,
            COUNT(*) AS catalyst_entry_count,
            COUNT(DISTINCT r.reaction_id) AS reaction_count
        FROM reactions AS r, json_each(r.catalysts_json) AS c
        {where_sql}
        GROUP BY catalyst_smiles, catalyst_name
        HAVING catalyst_smiles <> '' OR catalyst_name <> ''
        ORDER BY reaction_count DESC, catalyst_entry_count DESC, catalyst_smiles, catalyst_name
        LIMIT ?
        """,
        params,
    )

    return {
        "tool": "catalyst_statistics",
        "filters": {
            "reaction_type": reaction_type,
            "source_dataset": source_dataset,
        },
        "limit": row_limit,
        "count": len(results),
        "results": results,
        "assumptions": [
            "Catalysts are extracted from reactions.catalysts_json.",
            "A catalyst entry is one catalyst object in ORD-derived reaction JSON.",
            "reaction_count counts distinct reactions containing that catalyst entry.",
        ],
    }


def yield_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize procedure yield percentages for matching reactions."""
    where_clauses: list[str] = []
    params: list[Any] = []
    table_expression = "procedures AS p"
    if reaction_type:
        where_clauses.append("p.reaction_type ILIKE ?")
        params.append(_like_pattern(reaction_type))
    if source_dataset:
        table_expression = "procedures AS p JOIN reactions AS r ON r.reaction_id = p.reaction_id"
        where_clauses.append("r.source_dataset ILIKE ?")
        params.append(_like_pattern(source_dataset))

    payload = _numeric_statistics(
        tool="yield_statistics",
        table_expression=table_expression,
        value_column="p.yield_percent",
        value_name="yield_percent",
        where_clauses=where_clauses,
        params=params,
        filters={"reaction_type": reaction_type, "source_dataset": source_dataset},
        assumptions=[
            "Yields are read from procedures.yield_percent.",
            "Null and non-finite yields are excluded from numeric statistics.",
            "No correction is applied for yield basis, scale, purity, or repeated experiments.",
            "Raw statistics include extreme outliers (>100%) present in ORD data.",
            "Use clean_statistics for chemically meaningful 0-100% range.",
        ],
        database_path=database_path,
    )
    payload["quality_checks"] = _fetch_one(
        database_path,
        f"""
        SELECT
            COALESCE(SUM(CASE WHEN p.yield_percent < 0 THEN 1 ELSE 0 END), 0)
                AS below_zero_count,
            COALESCE(SUM(CASE WHEN p.yield_percent > 100 THEN 1 ELSE 0 END), 0)
                AS above_hundred_count,
            COALESCE(SUM(CASE WHEN p.yield_percent BETWEEN 0 AND 100 THEN 1 ELSE 0 END), 0)
                AS valid_range_count
        FROM {table_expression}
        {_where_sql([*where_clauses, 'p.yield_percent IS NOT NULL AND isfinite(p.yield_percent)'])}
        """,
        params,
    )
    # Clean statistics: only valid 0-100% yields for meaningful summaries
    valid_where = _where_sql([*where_clauses, "p.yield_percent >= 0", "p.yield_percent <= 100"])
    payload["clean_statistics"] = _fetch_one(
        database_path,
        f"""
        SELECT
            COUNT(*) AS count,
            AVG(p.yield_percent) AS average,
            MEDIAN(p.yield_percent) AS median,
            MIN(p.yield_percent) AS minimum,
            MAX(p.yield_percent) AS maximum,
            STDDEV_SAMP(p.yield_percent) AS sample_stddev,
            quantile_cont(p.yield_percent, 0.25) AS p25,
            quantile_cont(p.yield_percent, 0.75) AS p75
        FROM {table_expression}
        {valid_where}
        """,
        params,
    )
    return payload



def temperature_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize procedure temperatures in Celsius for matching reactions."""
    where_clauses: list[str] = []
    params: list[Any] = []
    table_expression = "procedures AS p"
    if reaction_type:
        where_clauses.append("p.reaction_type ILIKE ?")
        params.append(_like_pattern(reaction_type))
    if source_dataset:
        table_expression = "procedures AS p JOIN reactions AS r ON r.reaction_id = p.reaction_id"
        where_clauses.append("r.source_dataset ILIKE ?")
        params.append(_like_pattern(source_dataset))

    payload = _numeric_statistics(
        tool="temperature_statistics",
        table_expression=table_expression,
        value_column="p.temperature_c",
        value_name="temperature_c",
        where_clauses=where_clauses,
        params=params,
        filters={"reaction_type": reaction_type, "source_dataset": source_dataset},
        assumptions=[
            "Temperatures are read from procedures.temperature_c.",
            "Null and non-finite temperatures are excluded from numeric statistics.",
            "Temperatures are treated as reported Celsius values from the existing dataset.",
            "The global median is 0°C because ~81% of records are at or below 0°C (likely default/unset values).",
            "Use clean_statistics for the chemically meaningful -100°C to 300°C range.",
        ],
        database_path=database_path,
    )
    # Clean statistics: chemically plausible range only
    valid_where = _where_sql([*where_clauses, "p.temperature_c >= -100", "p.temperature_c <= 300"])
    payload["clean_statistics"] = _fetch_one(
        database_path,
        f"""
        SELECT
            COUNT(*) AS count,
            AVG(p.temperature_c) AS average,
            MEDIAN(p.temperature_c) AS median,
            MIN(p.temperature_c) AS minimum,
            MAX(p.temperature_c) AS maximum,
            STDDEV_SAMP(p.temperature_c) AS sample_stddev,
            quantile_cont(p.temperature_c, 0.25) AS p25,
            quantile_cont(p.temperature_c, 0.75) AS p75
        FROM {table_expression}
        {valid_where}
        """,
        params,
    )
    return payload



def source_dataset_statistics(
    *,
    reaction_type: str | None = None,
    sort_by: str = "reaction_count",
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize reaction/procedure/yield coverage by ORD source dataset."""
    row_limit = _normalize_limit(limit)
    if sort_by not in ("reaction_count", "procedure_count", "yield_count", "temperature_count"):
        sort_by = "reaction_count"
    
    where_clauses, params = _reaction_filters(reaction_type=reaction_type)
    where_sql = _where_sql(where_clauses)
    params.append(row_limit)

    results = _fetch_all(
        database_path,
        f"""
        WITH procedure_counts AS (
            SELECT
                reaction_id,
                COUNT(*) AS procedure_count,
                COUNT(yield_percent) AS yield_count,
                COUNT(temperature_c) AS temperature_count
            FROM procedures
            GROUP BY reaction_id
        )
        SELECT
            r.source_dataset,
            COUNT(*) AS reaction_count,
            COALESCE(SUM(pc.procedure_count), 0) AS procedure_count,
            COALESCE(SUM(pc.yield_count), 0) AS yield_count,
            COALESCE(SUM(pc.temperature_count), 0) AS temperature_count
        FROM reactions AS r
        LEFT JOIN procedure_counts AS pc ON pc.reaction_id = r.reaction_id
        {where_sql}
        GROUP BY r.source_dataset
        ORDER BY {sort_by} DESC, r.source_dataset
        LIMIT ?
        """,
        params,
    )

    return {
        "tool": "source_dataset_statistics",
        "filters": {"reaction_type": reaction_type},
        "limit": row_limit,
        "count": len(results),
        "results": results,
        "assumptions": [
            "Source dataset coverage is computed from reactions.source_dataset.",
            "Procedure, yield, and temperature counts are joined by reaction_id.",
        ],
    }


def reaction_type_statistics(
    *,
    source_dataset: str | None = None,
    sort_by: str = "reaction_count",
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize reaction/procedure/yield coverage by reaction type."""
    row_limit = _normalize_limit(limit)
    if sort_by not in ("reaction_count", "procedure_count", "yield_count", "temperature_count"):
        sort_by = "reaction_count"
        
    where_clauses, params = _reaction_filters(source_dataset=source_dataset)
    where_sql = _where_sql(where_clauses)
    params.append(row_limit)

    results = _fetch_all(
        database_path,
        f"""
        WITH procedure_counts AS (
            SELECT
                reaction_id,
                COUNT(*) AS procedure_count,
                COUNT(yield_percent) AS yield_count,
                COUNT(temperature_c) AS temperature_count
            FROM procedures
            GROUP BY reaction_id
        )
        SELECT
            r.reaction_type,
            COUNT(*) AS reaction_count,
            COALESCE(SUM(pc.procedure_count), 0) AS procedure_count,
            COALESCE(SUM(pc.yield_count), 0) AS yield_count,
            COALESCE(SUM(pc.temperature_count), 0) AS temperature_count
        FROM reactions AS r
        LEFT JOIN procedure_counts AS pc ON pc.reaction_id = r.reaction_id
        {where_sql}
        GROUP BY r.reaction_type
        ORDER BY {sort_by} DESC, r.reaction_type
        LIMIT ?
        """,
        params,
    )

    return {
        "tool": "reaction_type_statistics",
        "filters": {"source_dataset": source_dataset},
        "limit": row_limit,
        "count": len(results),
        "results": results,
        "assumptions": [
            "Reaction type coverage is computed from reactions.reaction_type.",
            "Procedure, yield, and temperature counts are joined by reaction_id.",
        ],
    }


def dataset_summary(
    *,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return high-level chemistry dataset coverage for the local ORD database."""
    counts = _fetch_one(
        database_path,
        """
        SELECT
            (SELECT COUNT(*) FROM reactions) AS reaction_count,
            (SELECT COUNT(*) FROM procedures) AS procedure_count,
            (SELECT COUNT(*) FROM molecules) AS molecule_count,
            (SELECT COUNT(DISTINCT reaction_type) FROM reactions) AS reaction_type_count,
            (SELECT COUNT(DISTINCT source_dataset) FROM reactions) AS source_dataset_count
        """,
    )
    coverage = _fetch_one(
        database_path,
        """
        SELECT
            SUM(CASE WHEN json_array_length(catalysts_json) > 0 THEN 1 ELSE 0 END)
                AS reactions_with_catalysts,
            SUM(CASE WHEN json_array_length(products_json) > 0 THEN 1 ELSE 0 END)
                AS reactions_with_products,
            SUM(CASE WHEN json_array_length(reactants_json) > 0 THEN 1 ELSE 0 END)
                AS reactions_with_reactants
        FROM reactions
        """,
    )
    procedure_coverage = _fetch_one(
        database_path,
        """
        SELECT
            COUNT(yield_percent) AS procedures_with_yield,
            SUM(
                CASE
                    WHEN yield_percent IS NOT NULL AND isfinite(yield_percent)
                    THEN 1
                    ELSE 0
                END
            ) AS procedures_with_finite_yield,
            COUNT(temperature_c) AS procedures_with_temperature,
            SUM(
                CASE
                    WHEN temperature_c IS NOT NULL AND isfinite(temperature_c)
                    THEN 1
                    ELSE 0
                END
            ) AS procedures_with_finite_temperature
        FROM procedures
        """,
    )

    return {
        "tool": "dataset_summary",
        "counts": counts,
        "reaction_coverage": coverage,
        "procedure_coverage": procedure_coverage,
        "assumptions": [
            "Counts are computed from the live DuckDB tables.",
            "Reaction coverage uses JSON array length checks on preserved chemistry fields.",
            "Procedure coverage reports both non-null and finite normalized scalar fields.",
        ],
    }


def reagent_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Rank reagent entries by occurrence and distinct reaction coverage.
    
    Reagents include solvents and other additives stored in reactions.reagents_json.
    """
    row_limit = _normalize_limit(limit)
    where_clauses, params = _reaction_filters(reaction_type, source_dataset)
    where_clauses.append("json_array_length(r.reagents_json) > 0")
    where_sql = _where_sql(where_clauses)
    params.append(row_limit)

    results = _fetch_all(
        database_path,
        f"""
        SELECT
            COALESCE(json_extract_string(rg.value, '$.smiles'), '') AS reagent_smiles,
            COALESCE(json_extract_string(rg.value, '$.name'), '') AS reagent_name,
            COUNT(*) AS reagent_entry_count,
            COUNT(DISTINCT r.reaction_id) AS reaction_count
        FROM reactions AS r, json_each(r.reagents_json) AS rg
        {where_sql}
        GROUP BY reagent_smiles, reagent_name
        HAVING reagent_smiles <> '' OR reagent_name <> ''
        ORDER BY reaction_count DESC, reagent_entry_count DESC, reagent_smiles, reagent_name
        LIMIT ?
        """,
        params,
    )

    return {
        "tool": "reagent_statistics",
        "filters": {
            "reaction_type": reaction_type,
            "source_dataset": source_dataset,
        },
        "limit": row_limit,
        "count": len(results),
        "results": results,
        "assumptions": [
            "Reagents are extracted from reactions.reagents_json.",
            "This includes solvents, bases, and other additives classified as reagents in ORD.",
            "reaction_count counts distinct reactions containing that reagent entry.",
        ],
    }


def compare_datasets(
    *,
    group_by: str = "source_dataset",
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compare high-level statistics across different datasets or reaction types."""
    if group_by not in ("source_dataset", "reaction_type"):
        group_by = "source_dataset"

    results = _fetch_all(
        database_path,
        f"""
        WITH procedure_counts AS (
            SELECT
                reaction_id,
                COUNT(*) AS procedure_count,
                COUNT(yield_percent) AS yield_count,
                AVG(yield_percent) AS avg_yield,
                AVG(temperature_c) AS avg_temperature
            FROM procedures
            GROUP BY reaction_id
        )
        SELECT
            r.{group_by} AS dataset_name,
            COUNT(DISTINCT r.reaction_id) AS reaction_count,
            COALESCE(SUM(pc.procedure_count), 0) AS procedure_count,
            COALESCE(AVG(pc.avg_yield), 0) AS avg_yield,
            COALESCE(AVG(pc.avg_temperature), 0) AS avg_temperature
        FROM reactions AS r
        LEFT JOIN procedure_counts AS pc ON pc.reaction_id = r.reaction_id
        WHERE r.{group_by} IS NOT NULL AND r.{group_by} != ''
        GROUP BY r.{group_by}
        ORDER BY reaction_count DESC
        LIMIT 50
        """,
    )

    return {
        "tool": "compare_datasets",
        "filters": {"group_by": group_by},
        "count": len(results),
        "results": results,
        "assumptions": [
            f"Comparing based on {group_by}.",
            "Averages are computed across procedures that have non-null values.",
        ],
    }


def top_yield_conditions(
    *,
    reaction_type: str | None = None,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Extract optimal reaction conditions (catalyst, temp) yielding the highest average yields."""
    where_clauses, params = _reaction_filters(reaction_type)
    where_clauses.append("r.reaction_type IS NOT NULL")
    where_clauses.append("p.yield_percent IS NOT NULL")
    where_sql = _where_sql(where_clauses)
    
    results = _fetch_all(
        database_path,
        f"""
        SELECT 
            r.reaction_type,
            c.catalyst as catalyst,
            COUNT(*) as freq,
            AVG(p.yield_percent) as avg_yield
        FROM reactions r
        JOIN procedures p ON r.reaction_id = p.reaction_id
        JOIN (
          SELECT reaction_id, unnest(from_json(catalysts_json, '["VARCHAR"]')) as catalyst 
          FROM reactions
          WHERE catalysts_json IS NOT NULL AND json_array_length(catalysts_json) > 0
        ) c ON c.reaction_id = r.reaction_id
        {where_sql}
        GROUP BY r.reaction_type, c.catalyst
        HAVING COUNT(*) >= 5
        ORDER BY avg_yield DESC
        LIMIT 20
        """,
        params,
    )

    return {
        "tool": "top_yield_conditions",
        "filters": {"reaction_type": reaction_type},
        "count": len(results),
        "results": results,
        "assumptions": [
            "Yield conditions are extracted for explicit reaction_type.",
            "Requires at least 5 reported yields for statistical significance.",
        ],
    }


def dataset_quality_report(
    *,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate a data quality report profiling nullability and metadata completeness."""
    results = _fetch_one(
        database_path,
        """
        SELECT
            COUNT(r.reaction_id) as total_reactions,
            SUM(CASE WHEN r.reaction_type IS NOT NULL THEN 1 ELSE 0 END) as reactions_with_type,
            COUNT(p.reaction_id) as total_procedures,
            SUM(CASE WHEN p.yield_percent IS NOT NULL THEN 1 ELSE 0 END) as procedures_with_yield,
            SUM(CASE WHEN p.temperature_c IS NOT NULL THEN 1 ELSE 0 END) as procedures_with_temp
        FROM reactions r
        LEFT JOIN procedures p ON r.reaction_id = p.reaction_id
        """,
    )

    return {
        "tool": "dataset_quality_report",
        "filters": {},
        "results": results,
        "assumptions": [
            "Profiles exact nullability counts across reactions and procedures.",
        ],
    }

