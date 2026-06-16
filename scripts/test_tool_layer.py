"""Smoke tests for the DuckDB-backed chemistry tool layer."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.tools import molecule_lookup, search_procedures, search_reactions


def assert_nonempty_result(name: str, payload: dict) -> None:
    assert payload["count"] > 0, f"{name} returned no rows"
    assert len(payload["results"]) == payload["count"]


def test_search_reactions() -> None:
    payload = search_reactions(
        reaction_type="Buchwald-Hartwig",
        catalyst="Pd",
        limit=3,
    )
    assert payload["tool"] == "search_reactions"
    assert payload["limit"] == 3
    assert_nonempty_result("search_reactions", payload)
    first = payload["results"][0]
    assert "reaction_id" in first
    assert isinstance(first["reactants_json"], list)
    assert isinstance(first["conditions_json"], dict)


def test_search_procedures() -> None:
    payload = search_procedures(
        reaction_type="Buchwald-Hartwig",
        text="cesium carbonate",
        temperature_min=80,
        yield_min=1,
        limit=3,
    )
    assert payload["tool"] == "search_procedures"
    assert payload["limit"] == 3
    assert_nonempty_result("search_procedures", payload)
    first = payload["results"][0]
    assert "procedure_text" in first
    assert first["temperature_c"] is None or first["temperature_c"] >= 80


def test_molecule_lookup() -> None:
    payload = molecule_lookup(smiles="Cl", limit=1)
    assert payload["tool"] == "molecule_lookup"
    assert payload["count"] == 1
    assert payload["results"][0]["smiles"] == "Cl"
    assert payload["results"][0]["occurrences"] > 0


def main() -> int:
    test_search_reactions()
    test_search_procedures()
    test_molecule_lookup()
    print("Tool layer smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
