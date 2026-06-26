"""Smoke tests for the FastAPI analytics endpoint layer.

Validates that every analytics endpoint:
- Returns HTTP 200
- Returns the expected top-level keys and tool identifier
- Returns plausible data against the live DuckDB database

Run with:
    python scripts/test_analytics_endpoints.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from backend.api.main import create_app  # noqa: E402

client = TestClient(create_app())


def assert_ok(path: str, params: dict | None = None) -> dict:
    response = client.get(path, params=params or {})
    assert response.status_code == 200, (
        f"GET {path} returned {response.status_code}: {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# /analytics/catalysts
# ---------------------------------------------------------------------------


def test_analytics_catalysts_default() -> None:
    payload = assert_ok("/analytics/catalysts")
    assert payload["tool"] == "catalyst_statistics"
    assert payload["limit"] == 10
    assert payload["count"] >= 0
    assert isinstance(payload["results"], list)
    assert isinstance(payload["assumptions"], list)
    assert len(payload["assumptions"]) > 0


def test_analytics_catalysts_with_filters() -> None:
    payload = assert_ok(
        "/analytics/catalysts",
        {"reaction_type": "Buchwald-Hartwig", "limit": 5},
    )
    assert payload["tool"] == "catalyst_statistics"
    assert payload["limit"] == 5
    assert payload["count"] >= 0
    # All results should have the required fields
    for result in payload["results"]:
        assert "catalyst_smiles" in result
        assert "catalyst_name" in result
        assert "catalyst_entry_count" in result
        assert "reaction_count" in result


def test_analytics_catalysts_result_ordering() -> None:
    """Results should be ordered by reaction_count descending."""
    payload = assert_ok("/analytics/catalysts", {"limit": 5})
    counts = [r["reaction_count"] for r in payload["results"]]
    assert counts == sorted(counts, reverse=True), (
        "Catalyst results are not ordered by reaction_count DESC"
    )


def test_analytics_catalysts_limit_validation() -> None:
    response = client.get("/analytics/catalysts", params={"limit": 0})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /analytics/yields
# ---------------------------------------------------------------------------


def test_analytics_yields_default() -> None:
    payload = assert_ok("/analytics/yields")
    assert payload["tool"] == "yield_statistics"
    assert payload["metric"] == "yield_percent"
    coverage = payload["coverage"]
    assert coverage["total_records"] > 0
    assert coverage["records_with_value"] >= 0
    assert coverage["records_with_finite_value"] >= 0
    stats = payload["statistics"]
    assert "count" in stats
    assert "average" in stats
    assert "median" in stats
    assert "minimum" in stats
    assert "maximum" in stats
    assert "sample_stddev" in stats
    assert "p25" in stats
    assert "p75" in stats
    quality = payload["quality_checks"]
    assert "below_zero_count" in quality
    assert "above_hundred_count" in quality
    assert isinstance(payload["assumptions"], list)


def test_analytics_yields_with_reaction_type() -> None:
    payload = assert_ok("/analytics/yields", {"reaction_type": "Buchwald-Hartwig"})
    assert payload["tool"] == "yield_statistics"
    assert payload["filters"]["reaction_type"] == "Buchwald-Hartwig"


def test_analytics_yields_value_sanity() -> None:
    """Finite yield count must not exceed total records with a value."""
    payload = assert_ok("/analytics/yields")
    coverage = payload["coverage"]
    assert coverage["records_with_finite_value"] <= coverage["records_with_value"]
    assert coverage["records_with_value"] <= coverage["total_records"]


# ---------------------------------------------------------------------------
# /analytics/temperatures
# ---------------------------------------------------------------------------


def test_analytics_temperatures_default() -> None:
    payload = assert_ok("/analytics/temperatures")
    assert payload["tool"] == "temperature_statistics"
    assert payload["metric"] == "temperature_c"
    coverage = payload["coverage"]
    assert coverage["total_records"] > 0
    stats = payload["statistics"]
    assert "count" in stats
    assert "average" in stats
    assert isinstance(payload["assumptions"], list)


def test_analytics_temperatures_with_filters() -> None:
    payload = assert_ok(
        "/analytics/temperatures",
        {"reaction_type": "Buchwald-Hartwig"},
    )
    assert payload["tool"] == "temperature_statistics"
    assert payload["filters"]["reaction_type"] == "Buchwald-Hartwig"


def test_analytics_temperatures_value_sanity() -> None:
    """Finite temperature count must not exceed total records with a value."""
    payload = assert_ok("/analytics/temperatures")
    coverage = payload["coverage"]
    assert coverage["records_with_finite_value"] <= coverage["records_with_value"]
    assert coverage["records_with_value"] <= coverage["total_records"]


# ---------------------------------------------------------------------------
# /analytics/datasets
# ---------------------------------------------------------------------------


def test_analytics_datasets_default() -> None:
    payload = assert_ok("/analytics/datasets")
    assert payload["tool"] == "source_dataset_statistics"
    assert payload["limit"] == 10
    assert payload["count"] >= 0
    assert isinstance(payload["results"], list)
    for result in payload["results"]:
        assert "source_dataset" in result
        assert "reaction_count" in result
        assert "procedure_count" in result
        assert "yield_count" in result
        assert "temperature_count" in result


def test_analytics_datasets_ordering() -> None:
    """Results should be ordered by reaction_count descending."""
    payload = assert_ok("/analytics/datasets", {"limit": 5})
    counts = [r["reaction_count"] for r in payload["results"]]
    assert counts == sorted(counts, reverse=True), (
        "Dataset results are not ordered by reaction_count DESC"
    )


def test_analytics_datasets_count_matches_results() -> None:
    payload = assert_ok("/analytics/datasets", {"limit": 5})
    assert payload["count"] == len(payload["results"])


def test_analytics_datasets_limit_validation() -> None:
    response = client.get("/analytics/datasets", params={"limit": 0})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /analytics/reaction-types
# ---------------------------------------------------------------------------


def test_analytics_reaction_types_default() -> None:
    payload = assert_ok("/analytics/reaction-types")
    assert payload["tool"] == "reaction_type_statistics"
    assert payload["limit"] == 10
    assert payload["count"] >= 0
    assert isinstance(payload["results"], list)
    for result in payload["results"]:
        assert "reaction_type" in result
        assert "reaction_count" in result
        assert "procedure_count" in result
        assert "yield_count" in result
        assert "temperature_count" in result


def test_analytics_reaction_types_ordering() -> None:
    """Results should be ordered by reaction_count descending."""
    payload = assert_ok("/analytics/reaction-types", {"limit": 5})
    counts = [r["reaction_count"] for r in payload["results"]]
    assert counts == sorted(counts, reverse=True), (
        "Reaction type results are not ordered by reaction_count DESC"
    )


def test_analytics_reaction_types_count_matches_results() -> None:
    payload = assert_ok("/analytics/reaction-types", {"limit": 5})
    assert payload["count"] == len(payload["results"])


def test_analytics_reaction_types_limit_validation() -> None:
    response = client.get("/analytics/reaction-types", params={"limit": 0})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /analytics/summary
# ---------------------------------------------------------------------------


def test_analytics_summary() -> None:
    payload = assert_ok("/analytics/summary")
    assert payload["tool"] == "dataset_summary"
    counts = payload["counts"]
    assert counts["reaction_count"] == 2_376_120
    assert counts["procedure_count"] == 1_788_170
    assert counts["molecule_count"] == 1_993_180
    assert counts["reaction_type_count"] > 0
    assert counts["source_dataset_count"] > 0
    reaction_cov = payload["reaction_coverage"]
    assert "reactions_with_catalysts" in reaction_cov
    assert "reactions_with_products" in reaction_cov
    assert "reactions_with_reactants" in reaction_cov
    proc_cov = payload["procedure_coverage"]
    assert "procedures_with_yield" in proc_cov
    assert "procedures_with_finite_yield" in proc_cov
    assert "procedures_with_temperature" in proc_cov
    assert "procedures_with_finite_temperature" in proc_cov
    assert isinstance(payload["assumptions"], list)


def test_analytics_summary_record_counts_are_positive() -> None:
    payload = assert_ok("/analytics/summary")
    counts = payload["counts"]
    for field, value in counts.items():
        assert value > 0, f"Expected {field} > 0, got {value}"


def test_analytics_summary_coverage_sanity() -> None:
    """Coverage counts must not exceed total record counts."""
    payload = assert_ok("/analytics/summary")
    total_reactions = payload["counts"]["reaction_count"]
    cov = payload["reaction_coverage"]
    assert cov["reactions_with_catalysts"] <= total_reactions
    assert cov["reactions_with_products"] <= total_reactions
    assert cov["reactions_with_reactants"] <= total_reactions

    total_procedures = payload["counts"]["procedure_count"]
    proc_cov = payload["procedure_coverage"]
    assert proc_cov["procedures_with_yield"] <= total_procedures
    assert proc_cov["procedures_with_finite_yield"] <= proc_cov["procedures_with_yield"]
    assert proc_cov["procedures_with_temperature"] <= total_procedures
    assert proc_cov["procedures_with_finite_temperature"] <= proc_cov["procedures_with_temperature"]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def main() -> int:
    tests = [
        test_analytics_catalysts_default,
        test_analytics_catalysts_with_filters,
        test_analytics_catalysts_result_ordering,
        test_analytics_catalysts_limit_validation,
        test_analytics_yields_default,
        test_analytics_yields_with_reaction_type,
        test_analytics_yields_value_sanity,
        test_analytics_temperatures_default,
        test_analytics_temperatures_with_filters,
        test_analytics_temperatures_value_sanity,
        test_analytics_datasets_default,
        test_analytics_datasets_ordering,
        test_analytics_datasets_count_matches_results,
        test_analytics_datasets_limit_validation,
        test_analytics_reaction_types_default,
        test_analytics_reaction_types_ordering,
        test_analytics_reaction_types_count_matches_results,
        test_analytics_reaction_types_limit_validation,
        test_analytics_summary,
        test_analytics_summary_record_counts_are_positive,
        test_analytics_summary_coverage_sanity,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {test.__name__}: {exc}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
