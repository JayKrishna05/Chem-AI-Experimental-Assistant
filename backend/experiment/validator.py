"""Validator for CanonicalExperiments."""

from __future__ import annotations

from backend.experiment.models import CanonicalExperiment, ValidationResult


def validate_experiment(
    exp: CanonicalExperiment, 
    normalized_fields: list[str] | None = None
) -> ValidationResult:
    """Validate a canonical experiment without mutating it.
    
    Returns a ValidationResult with non-fatal warnings and a confidence score.
    """
    warnings = []
    missing_fields = []
    confidence = 1.0
    
    # Check core chemistry fields
    if not exp.reactants:
        warnings.append("No reactants identified.")
        missing_fields.append("reactants")
        confidence -= 0.2
        
    if not exp.products:
        warnings.append("No products identified.")
        missing_fields.append("products")
        confidence -= 0.2
        
    if not exp.reaction_type:
        missing_fields.append("reaction_type")
        confidence -= 0.1
        
    # Check procedure conditions
    if exp.temperature_c is None:
        missing_fields.append("temperature_c")
    elif exp.temperature_c < -100 or exp.temperature_c > 300:
        warnings.append(f"Temperature {exp.temperature_c}°C is highly unusual.")
        confidence -= 0.1

    if exp.yield_percent is None:
        missing_fields.append("yield_percent")
        confidence -= 0.1
    elif exp.yield_percent > 100:
        warnings.append(f"Yield {exp.yield_percent}% exceeds 100%.")
        confidence -= 0.2
        
    # Is it completely invalid?
    is_valid = True
    if not exp.reactants and not exp.products and exp.yield_percent is None:
        warnings.append("Experiment appears completely empty or failed to parse.")
        is_valid = False
        confidence = 0.0

    return ValidationResult(
        experiment=exp,
        warnings=warnings,
        confidence_score=max(0.0, round(confidence, 2)),
        normalized_fields=normalized_fields or [],
        missing_fields=missing_fields,
        is_valid=is_valid,
    )
