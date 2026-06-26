"""Smoke tests for the FastAPI experiment endpoints."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.main import create_app

client = TestClient(create_app())


def test_parse_json_endpoint() -> None:
    payload = {
        "content": '{"reaction_type": "Suzuki", "reactants": ["benzene"], "temperature_c": 100}',
        "format": "json"
    }
    response = client.post("/experiments/parse", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["is_valid"] is True
    assert len(data["experiments"]) == 1
    exp = data["experiments"][0]
    assert exp["reaction_type"] == "Suzuki"
    assert exp["reactants"] == ["benzene"]


def test_parse_csv_endpoint() -> None:
    payload = {
        "content": "type,temp,yield\nSuzuki,100,90\n",
        "format": "csv"
    }
    response = client.post("/experiments/parse", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["experiments"]) == 1
    exp = data["experiments"][0]
    assert exp["reaction_type"] == "Suzuki"
    assert exp["temperature_c"] == 100.0


def test_compare_endpoint() -> None:
    payload = {
        "content": '{"reaction_type": "Buchwald-Hartwig", "reactants": ["bromobenzene"], "temperature_c": 100, "yield_percent": 90.0, "products": ["aniline"]}',
        "format": "json"
    }
    response = client.post("/experiments/compare", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["comparisons"]) == 1
    comp = data["comparisons"][0]
    assert comp["is_valid"] is True
    assert "similar_reactions" in comp["comparisons"]
    # Depending on the test DB, optimal_conditions or temperature_profile might not be populated
    # so we avoid rigid assertions on them if they require specific data thresholds.


def main() -> int:
    test_parse_json_endpoint()
    test_parse_csv_endpoint()
    test_compare_endpoint()
    print("API endpoint smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
