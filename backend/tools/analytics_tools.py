"""DuckDB-backed analytics tools for ORD chemistry and procedures.
Now acts as a thin formatting layer over StatisticsRepository.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from backend.tools.filters import CommonFilters, build_limit, format_tool_response
from backend.database.repositories.statistics_repository import StatisticsRepository

DEFAULT_LIMIT = 10
MAX_LIMIT = 100

def catalyst_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Rank catalyst entries by occurrence and distinct reaction coverage."""
    start_time = time.time()
    row_limit = build_limit(limit, MAX_LIMIT)
    applied_filters = {"reaction_type": reaction_type, "source_dataset": source_dataset}
    filters_model = CommonFilters(**applied_filters)
    
    repo = StatisticsRepository(database_path)
    results, total_rows = repo.get_catalyst_statistics(filters_model, row_limit)

    return format_tool_response(
        tool_name="catalyst_statistics",
        applied_filters=applied_filters,
        results=results,
        total_matching_rows=total_rows,
        limit=row_limit,
        assumptions=[
            "Catalysts are extracted from reactions.catalysts_json.",
            "A catalyst entry is one catalyst object in ORD-derived reaction JSON.",
            "reaction_count counts distinct reactions containing that catalyst entry.",
        ],
        start_time=start_time,
    )

def yield_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize procedure yield percentages for matching reactions."""
    start_time = time.time()
    applied_filters = {"reaction_type": reaction_type, "source_dataset": source_dataset}
    filters_model = CommonFilters(**applied_filters)
    
    repo = StatisticsRepository(database_path)
    payload = repo.get_yield_statistics(filters_model)
    
    # We construct the response using the coverage numbers
    # The numeric_statistics base function returned `results` as the payload.
    # format_tool_response needs total_matching_rows.
    total_rows = payload.get("coverage", {}).get("total_records", 0)

    # To maintain backwards compatibility of the tool contract
    payload["metric"] = "yield_percent"

    return format_tool_response(
        tool_name="yield_statistics",
        applied_filters=applied_filters,
        results=payload,
        total_matching_rows=total_rows,
        assumptions=[
            "Yields are read from procedures.yield_percent.",
            "Null and non-finite yields are excluded from numeric statistics.",
            "No correction is applied for yield basis, scale, purity, or repeated experiments.",
            "Raw statistics include extreme outliers (>100%) present in ORD data.",
            "Use clean_statistics for chemically meaningful 0-100% range.",
        ],
        start_time=start_time,
    )

def temperature_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize procedure temperatures in Celsius for matching reactions."""
    start_time = time.time()
    applied_filters = {"reaction_type": reaction_type, "source_dataset": source_dataset}
    filters_model = CommonFilters(**applied_filters)
    
    repo = StatisticsRepository(database_path)
    payload = repo.get_temperature_statistics(filters_model)
    
    total_rows = payload.get("coverage", {}).get("total_records", 0)
    payload["metric"] = "temperature_c"

    return format_tool_response(
        tool_name="temperature_statistics",
        applied_filters=applied_filters,
        results=payload,
        total_matching_rows=total_rows,
        assumptions=[
            "Temperatures are read from procedures.temperature_c.",
            "Null and non-finite temperatures are excluded from numeric statistics.",
            "Temperatures are treated as reported Celsius values from the existing dataset.",
            "The global median is 0°C because ~81% of records are at or below 0°C (likely default/unset values).",
            "Use clean_statistics for the chemically meaningful -100°C to 300°C range.",
        ],
        start_time=start_time,
    )

def source_dataset_statistics(
    *,
    reaction_type: str | None = None,
    sort_by: str = "reaction_count",
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize reaction/procedure/yield coverage by ORD source dataset."""
    start_time = time.time()
    row_limit = build_limit(limit, MAX_LIMIT)
    applied_filters = {"reaction_type": reaction_type, "sort_by": sort_by}
    
    if sort_by not in ("reaction_count", "procedure_count", "yield_count", "temperature_count"):
        sort_by = "reaction_count"
        
    filters_model = CommonFilters(reaction_type=reaction_type)
    
    repo = StatisticsRepository(database_path)
    results, total_rows = repo.get_source_dataset_statistics(filters_model, sort_by, row_limit)

    return format_tool_response(
        tool_name="source_dataset_statistics",
        applied_filters=applied_filters,
        results=results,
        total_matching_rows=total_rows,
        limit=row_limit,
        assumptions=[
            "Source dataset coverage is computed from reactions.source_dataset.",
            "Procedure, yield, and temperature counts are joined by reaction_id.",
        ],
        start_time=start_time,
    )

def reaction_type_statistics(
    *,
    source_dataset: str | None = None,
    sort_by: str = "reaction_count",
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize reaction/procedure/yield coverage by reaction type."""
    start_time = time.time()
    row_limit = build_limit(limit, MAX_LIMIT)
    applied_filters = {"source_dataset": source_dataset, "sort_by": sort_by}
    
    if sort_by not in ("reaction_count", "procedure_count", "yield_count", "temperature_count"):
        sort_by = "reaction_count"
        
    filters_model = CommonFilters(source_dataset=source_dataset)
    
    repo = StatisticsRepository(database_path)
    results, total_rows = repo.get_reaction_type_statistics(filters_model, sort_by, row_limit)

    return format_tool_response(
        tool_name="reaction_type_statistics",
        applied_filters=applied_filters,
        results=results,
        total_matching_rows=total_rows,
        limit=row_limit,
        assumptions=[
            "Reaction type coverage is computed from reactions.reaction_type.",
            "Procedure, yield, and temperature counts are joined by reaction_id.",
        ],
        start_time=start_time,
    )

def dataset_summary(
    *,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return high-level chemistry dataset coverage for the local ORD database."""
    start_time = time.time()
    
    repo = StatisticsRepository(database_path)
    results_dict = repo.get_dataset_summary()
    
    total_rows = results_dict.get("counts", {}).get("reaction_count", 0)

    return format_tool_response(
        tool_name="dataset_summary",
        applied_filters={},
        results=results_dict,
        total_matching_rows=total_rows,
        assumptions=[
            "Counts are computed from the live DuckDB tables.",
            "Reaction coverage uses JSON array length checks on preserved chemistry fields.",
            "Procedure coverage reports both non-null and finite normalized scalar fields.",
        ],
        start_time=start_time,
    )

def reagent_statistics(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    limit: int = DEFAULT_LIMIT,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Rank reagent entries by occurrence and distinct reaction coverage."""
    start_time = time.time()
    row_limit = build_limit(limit, MAX_LIMIT)
    applied_filters = {"reaction_type": reaction_type, "source_dataset": source_dataset}
    filters_model = CommonFilters(**applied_filters)
    
    repo = StatisticsRepository(database_path)
    results, total_rows = repo.get_reagent_statistics(filters_model, row_limit)

    return format_tool_response(
        tool_name="reagent_statistics",
        applied_filters=applied_filters,
        results=results,
        total_matching_rows=total_rows,
        limit=row_limit,
        assumptions=[
            "Reagents are extracted from reactions.reagents_json.",
            "This includes solvents, bases, and other additives classified as reagents in ORD.",
            "reaction_count counts distinct reactions containing that reagent entry.",
        ],
        start_time=start_time,
    )

def compare_datasets(
    *,
    group_by: str = "source_dataset",
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    catalyst: str | None = None,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compare high-level statistics across different datasets or reaction types."""
    start_time = time.time()
    if group_by not in ("source_dataset", "reaction_type"):
        group_by = "source_dataset"

    applied_filters = {
        "group_by": group_by,
        "reaction_type": reaction_type,
        "source_dataset": source_dataset,
        "catalyst": catalyst,
    }
    filters_model = CommonFilters(reaction_type=reaction_type, source_dataset=source_dataset, catalyst=catalyst)
    
    repo = StatisticsRepository(database_path)
    results, total_rows = repo.get_compare_datasets(filters_model, group_by)

    return format_tool_response(
        tool_name="compare_datasets",
        applied_filters=applied_filters,
        results=results,
        total_matching_rows=total_rows,
        limit=50,
        assumptions=[
            f"Comparing based on {group_by}.",
            "Averages are computed across procedures that have non-null values.",
        ],
        start_time=start_time,
    )

def top_yield_conditions(
    *,
    reaction_type: str | None = None,
    source_dataset: str | None = None,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Extract optimal reaction conditions (catalyst, temp) yielding the highest average yields."""
    start_time = time.time()
    applied_filters = {"reaction_type": reaction_type, "source_dataset": source_dataset}
    filters_model = CommonFilters(**applied_filters)
    
    repo = StatisticsRepository(database_path)
    results, total_rows = repo.get_top_yield_conditions(filters_model)

    return format_tool_response(
        tool_name="top_yield_conditions",
        applied_filters=applied_filters,
        results=results,
        total_matching_rows=total_rows,
        limit=20,
        assumptions=[
            "Yield conditions are extracted for explicitly matching reactions.",
            "Requires at least 5 reported yields for statistical significance.",
        ],
        start_time=start_time,
    )

def dataset_quality_report(
    *,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate a data quality report profiling nullability and metadata completeness."""
    start_time = time.time()
    repo = StatisticsRepository(database_path)
    results = repo.get_dataset_quality_report()

    return format_tool_response(
        tool_name="dataset_quality_report",
        applied_filters={},
        results=results,
        total_matching_rows=results.get("total_reactions", 0) if results else 0,
        assumptions=[
            "Profiles exact nullability counts across reactions and procedures.",
        ],
        start_time=start_time,
    )
