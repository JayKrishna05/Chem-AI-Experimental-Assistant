"""Smoke tests for the FastAPI endpoint layer."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.main import create_app


client = TestClient(create_app())


def assert_ok(path: str, params: dict | None = None) -> dict:
    response = client.get(path, params=params or {})
    assert response.status_code == 200, response.text
    return response.json()


def test_health() -> None:
    payload = assert_ok("/health")
    assert payload["status"] == "ok"
    assert payload["database_available"] is True


def test_reactions_search() -> None:
    payload = assert_ok(
        "/reactions/search",
        {"reaction_type": "Buchwald-Hartwig", "catalyst": "Pd", "limit": 2},
    )
    assert payload["tool"] == "search_reactions"
    assert payload["count"] > 0
    assert payload["count"] <= 2
    assert "reactants_json" in payload["results"][0]


def test_procedures_search() -> None:
    payload = assert_ok(
        "/procedures/search",
        {
            "reaction_type": "Buchwald-Hartwig",
            "text": "cesium carbonate",
            "temperature_min": 80,
            "limit": 2,
        },
    )
    assert payload["tool"] == "search_procedures"
    assert payload["count"] > 0
    assert payload["count"] <= 2
    assert "procedure_text" in payload["results"][0]


def test_molecules_search() -> None:
    payload = assert_ok("/molecules/search", {"smiles": "Cl", "limit": 1})
    assert payload["tool"] == "molecule_lookup"
    assert payload["count"] == 1
    assert payload["results"][0]["smiles"] == "Cl"


def test_validation_error() -> None:
    response = client.get("/molecules/search", params={"limit": 0})
    assert response.status_code == 422


def main() -> int:
    test_health()
    test_reactions_search()
    test_procedures_search()
    test_molecules_search()
    test_validation_error()
    print("API endpoint smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
