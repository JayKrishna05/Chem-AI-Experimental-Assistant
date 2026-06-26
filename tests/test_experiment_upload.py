"""Tests for the Phase 5 experiment upload and comparison pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.experiment.models import CanonicalExperiment
from backend.experiment.parser import dispatch_parse
from backend.experiment.normalizer import normalize_experiment
from backend.experiment.validator import validate_experiment


def test_models():
    exp = CanonicalExperiment(reaction_type="Suzuki", yield_percent=85.5)
    assert exp.reaction_type == "Suzuki"
    assert exp.yield_percent == 85.5
    assert exp.experiment_id is not None
    assert exp.schema_version == "1.0"


def test_dispatch_parse_json():
    data = json.dumps({
        "reaction_type": "Buchwald Hartwig",
        "reactants": ["bromobenzene", "aniline"],
        "catalysts": ["palladium"],
        "temperature_c": 100,
        "yield_percent": 95
    })
    exps, _ = dispatch_parse(data.encode('utf-8'), 'file.json')
    exp = exps[0]
    assert exp.reaction_type == "Buchwald Hartwig"
    assert exp.temperature_c == 100
    assert exp.catalysts == ["palladium"]


def test_dispatch_parse_csv():
    csv_data = "type,reactant,catalyst,temp,yield %\nSuzuki,benzene,Pd,80,90\n"
    exps, _ = dispatch_parse(csv_data.encode('utf-8'), 'file.csv')
    assert len(exps) == 1
    exp = exps[0]
    assert exp.reaction_type == "Suzuki"
    assert exp.reactants == ["benzene"]
    assert exp.catalysts == ["Pd"]
    assert exp.temperature_c == 80
    assert exp.yield_percent == 90


def test_dispatch_parse_text():
    text_data = "The reaction was run at 65.5 C and gave an 85% yield."
    exps, _ = dispatch_parse(text_data.encode('utf-8'), 'file.txt')
    exp = exps[0]
    assert exp.temperature_c == 65.5
    assert exp.yield_percent == 85


def test_normalizer():
    exp = CanonicalExperiment(
        reaction_type="buchwald hartwig",
        catalysts=["PALLADIUM"],
        reactants=[" A ", "B"],
        yield_percent=-10
    )
    norm_exp, fields = normalize_experiment(exp)
    assert norm_exp.reaction_type == "Buchwald-Hartwig"
    assert norm_exp.catalysts == ["Pd"]
    assert norm_exp.reactants == ["A", "B"]
    assert norm_exp.yield_percent == 0.0
    assert "reaction_type" in fields
    assert "catalysts" in fields
    assert "reactants" in fields
    assert "yield_percent" in fields


def test_validator():
    exp = CanonicalExperiment(
        reaction_type="Suzuki",
        reactants=["A"],
        products=["B"],
        temperature_c=25,
        yield_percent=105
    )
    res = validate_experiment(exp)
    assert res.is_valid is True
    assert len(res.warnings) > 0
    assert "exceeds 100%" in res.warnings[0]
    assert res.confidence_score < 1.0


def test_empty_validator():
    exp = CanonicalExperiment()
    res = validate_experiment(exp)
    assert res.is_valid is False
    assert "missing_fields" in res.model_dump()
    assert "reaction_type" in res.missing_fields


# --- STRESS TESTS ---

def test_parser_stress_csv_alternative_columns():
    # Test alternative columns, inconsistent caps, and trailing spaces
    csv_data = "Reaction_Type, REACTANT , CATALYST, Temperature , Yield %\nSuzuki,benzene,Pd,80,90\n"
    exps, _ = dispatch_parse(csv_data.encode('utf-8'), 'file.csv')
    exp = exps[0]
    assert exp.reaction_type == "Suzuki"
    assert exp.reactants == ["benzene"]
    assert exp.temperature_c == 80.0
    assert exp.yield_percent == 90.0

def test_parser_stress_csv_mixed_units_and_malformed():
    # Test mixed units (e.g. 80 C instead of just 80), malformed numbers, and missing fields
    # Currently the parser uses float(temperature_c), so "80 C" will cause a ValueError and yield None.
    csv_data = "type,temp,yield\nHeck,80 C,95%\nAmide,N/A,\n"
    exps, _ = dispatch_parse(csv_data.encode('utf-8'), 'file.csv')
    assert len(exps) == 2
    
    # "80 C" fails float() conversion, so we expect None in MVP
    assert exps[0].temperature_c is None 
    assert exps[0].yield_percent is None
    
    assert exps[1].temperature_c is None
    assert exps[1].yield_percent is None

def test_parser_stress_aliases_and_duplicates():
    # Duplicate columns in csv.DictReader overwrite previous columns with the same name.
    # Catalyst alias "PALLADIUM" should be normalized.
    csv_data = "type,reactant,reactant,catalyst\nHeck,A,B,PALLADIUM\n"
    exps, _ = dispatch_parse(csv_data.encode('utf-8'), 'file.csv')
    exp = exps[0]
    # DictReader uses the last 'reactant' column
    assert exp.reactants == ["B"]
    
    # Run through normalizer
    norm_exp, _ = normalize_experiment(exp)
    assert norm_exp.catalysts == ["Pd"]

    
if __name__ == "__main__":
    test_models()
    test_dispatch_parse_json()
    test_dispatch_parse_csv()
    test_dispatch_parse_text()
    test_normalizer()
    test_validator()
    test_empty_validator()
    
    # Run stress tests
    test_parser_stress_csv_alternative_columns()
    test_parser_stress_csv_mixed_units_and_malformed()
    test_parser_stress_aliases_and_duplicates()
    print("All unit tests and stress tests for experiment components passed.")
