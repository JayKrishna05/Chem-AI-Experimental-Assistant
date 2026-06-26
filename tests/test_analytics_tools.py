"""Correctness checks for DuckDB-backed analytics tools."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.tools import (  # noqa: E402
    catalyst_statistics,
    dataset_summary,
    reaction_type_statistics,
    source_dataset_statistics,
    temperature_statistics,
    yield_statistics,
    compare_datasets,
    top_yield_conditions,
    dataset_quality_report,
)
from backend.tools.db import DEFAULT_DB_PATH  # noqa: E402


def direct_one(sql: str, params: list | None = None) -> dict:
    with duckdb.connect(str(DEFAULT_DB_PATH), read_only=True) as con:
        cursor = con.execute(sql, params or [])
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
    return dict(zip(columns, row, strict=True))


def direct_all(sql: str, params: list | None = None) -> list[dict]:
    with duckdb.connect(str(DEFAULT_DB_PATH), read_only=True) as con:
        cursor = con.execute(sql, params or [])
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
    return [dict(zip(columns, row, strict=True)) for row in rows]


def assert_close(actual: float | None, expected: float | None) -> None:
    if actual is None or expected is None:
        assert actual == expected
        return
    assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9), (
        actual,
        expected,
    )


def test_dataset_summary() -> None:
    payload = dataset_summary()
    expected = direct_one(
        """
        SELECT
            (SELECT COUNT(*) FROM reactions) AS reaction_count,
            (SELECT COUNT(*) FROM procedures) AS procedure_count,
            (SELECT COUNT(*) FROM molecules) AS molecule_count,
            (SELECT COUNT(DISTINCT reaction_type) FROM reactions) AS reaction_type_count,
            (SELECT COUNT(DISTINCT source_dataset) FROM reactions) AS source_dataset_count
        """
    )
    assert payload["counts"] == expected
    assert payload["counts"]["reaction_count"] == 2_376_120
    assert payload["counts"]["procedure_count"] == 1_788_170
    assert payload["counts"]["molecule_count"] == 1_993_180


def test_catalyst_statistics() -> None:
    payload = catalyst_statistics(reaction_type="Buchwald-Hartwig", limit=5)
    expected = direct_all(
        """
        SELECT
            COALESCE(json_extract_string(c.value, '$.smiles'), '') AS catalyst_smiles,
            COALESCE(json_extract_string(c.value, '$.name'), '') AS catalyst_name,
            COUNT(*) AS catalyst_entry_count,
            COUNT(DISTINCT r.reaction_id) AS reaction_count
        FROM reactions AS r, json_each(r.catalysts_json) AS c
        WHERE r.reaction_type ILIKE ?
          AND json_array_length(r.catalysts_json) > 0
        GROUP BY catalyst_smiles, catalyst_name
        HAVING catalyst_smiles <> '' OR catalyst_name <> ''
        ORDER BY reaction_count DESC, catalyst_entry_count DESC, catalyst_smiles, catalyst_name
        LIMIT 5
        """,
        ["%Buchwald-Hartwig%"],
    )
    assert payload["results"] == expected
    assert payload["count"] == len(expected)
    assert payload["count"] > 0


def test_yield_statistics() -> None:
    payload = yield_statistics(reaction_type="Buchwald-Hartwig")
    expected = direct_one(
        """
        SELECT
            COUNT(*) AS count,
            AVG(p.yield_percent) AS average,
            MEDIAN(p.yield_percent) AS median,
            MIN(p.yield_percent) AS minimum,
            MAX(p.yield_percent) AS maximum,
            STDDEV_SAMP(p.yield_percent) AS sample_stddev,
            quantile_cont(p.yield_percent, 0.25) AS p25,
            quantile_cont(p.yield_percent, 0.75) AS p75
        FROM procedures AS p
        WHERE p.reaction_type ILIKE ?
          AND p.yield_percent IS NOT NULL
          AND isfinite(p.yield_percent)
        """,
        ["%Buchwald-Hartwig%"],
    )
    for key, value in expected.items():
        if isinstance(value, float):
            assert_close(payload["statistics"][key], value)
        else:
            assert payload["statistics"][key] == value
    assert payload["statistics"]["count"] > 0


def test_temperature_statistics() -> None:
    payload = temperature_statistics(reaction_type="Buchwald-Hartwig")
    expected = direct_one(
        """
        SELECT
            COUNT(*) AS count,
            AVG(p.temperature_c) AS average,
            MEDIAN(p.temperature_c) AS median,
            MIN(p.temperature_c) AS minimum,
            MAX(p.temperature_c) AS maximum,
            STDDEV_SAMP(p.temperature_c) AS sample_stddev,
            quantile_cont(p.temperature_c, 0.25) AS p25,
            quantile_cont(p.temperature_c, 0.75) AS p75
        FROM procedures AS p
        WHERE p.reaction_type ILIKE ?
          AND p.temperature_c IS NOT NULL
          AND isfinite(p.temperature_c)
        """,
        ["%Buchwald-Hartwig%"],
    )
    for key, value in expected.items():
        if isinstance(value, float):
            assert_close(payload["statistics"][key], value)
        else:
            assert payload["statistics"][key] == value
    assert payload["statistics"]["count"] > 0


def test_yield_statistics_empty_filter() -> None:
    payload = yield_statistics(reaction_type="Suzuki")
    expected = direct_one(
        """
        SELECT
            COUNT(*) AS total_records,
            COUNT(p.yield_percent) AS records_with_value,
            COALESCE(SUM(
                CASE
                    WHEN p.yield_percent IS NOT NULL AND isfinite(p.yield_percent)
                    THEN 1
                    ELSE 0
                END
            ), 0) AS records_with_finite_value
        FROM procedures AS p
        WHERE p.reaction_type ILIKE ?
        """,
        ["%Suzuki%"],
    )
    assert payload["coverage"] == expected
    assert payload["statistics"]["count"] == 0
    assert payload["statistics"]["average"] is None


def test_source_dataset_statistics() -> None:
    payload = source_dataset_statistics(limit=5)
    expected = direct_all(
        """
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
        GROUP BY r.source_dataset
        ORDER BY reaction_count DESC, r.source_dataset
        LIMIT 5
        """
    )
    assert payload["results"] == expected
    assert payload["count"] == 5


def test_reaction_type_statistics() -> None:
    payload = reaction_type_statistics(limit=5)
    expected = direct_all(
        """
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
        GROUP BY r.reaction_type
        ORDER BY reaction_count DESC, r.reaction_type
        LIMIT 5
        """
    )
    assert payload["results"] == expected
    assert payload["count"] == 5


def main() -> int:
    test_dataset_summary()
    test_catalyst_statistics()
    test_yield_statistics()
    test_temperature_statistics()
    test_yield_statistics_empty_filter()
    test_source_dataset_statistics()
    test_reaction_type_statistics()
    print("Analytics tool validation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



def test_compare_datasets():
    print("Testing compare_datasets...")
    res = compare_datasets(group_by="source_dataset", database_path=DEFAULT_DB_PATH)
    assert res["tool"] == "compare_datasets"
    assert "results" in res
    assert len(res["results"]) > 0
    
    # Check shape of result
    first = res["results"][0]
    assert "dataset_name" in first
    assert "reaction_count" in first
    assert "avg_yield" in first

def test_top_yield_conditions():
    print("Testing top_yield_conditions...")
    res = top_yield_conditions(database_path=DEFAULT_DB_PATH)
    assert res["tool"] == "top_yield_conditions"
    assert "results" in res
    assert len(res["results"]) > 0
    
    # Check shape of result
    first = res["results"][0]
    assert "reaction_type" in first
    assert "catalyst" in first
    assert "avg_yield" in first

def test_dataset_quality_report():
    print("Testing dataset_quality_report...")
    res = dataset_quality_report(database_path=DB_PATH)
    assert res["tool"] == "dataset_quality_report"
    assert "total_reactions" in res
    assert "procedures_with_yield" in res

if __name__ == "__main__":
    test_compare_datasets()
    test_top_yield_conditions()
    test_dataset_quality_report()
    print("All tests passed.")
