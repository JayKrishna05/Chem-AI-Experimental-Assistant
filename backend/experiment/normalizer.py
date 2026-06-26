"""Normalizer for standardizing fields in a CanonicalExperiment."""

from __future__ import annotations

import copy
from typing import Any

from backend.experiment.models import CanonicalExperiment


def normalize_experiment(exp: CanonicalExperiment) -> tuple[CanonicalExperiment, list[str]]:
    """Normalize fields like catalyst naming, units, and aliases.
    
    Returns:
        A tuple of (normalized CanonicalExperiment, list of normalized field names).
    """
    normalized_exp = exp.model_copy(deep=True)
    normalized_fields = []

    # Helper to check if a value changed
    def _update_if_changed(field: str, old_val: Any, new_val: Any) -> None:
        if old_val != new_val:
            setattr(normalized_exp, field, new_val)
            normalized_fields.append(field)

    # Normalize reaction type
    if normalized_exp.reaction_type:
        new_type = normalized_exp.reaction_type.strip().title()
        if new_type.lower() == "buchwald hartwig":
            new_type = "Buchwald-Hartwig"
        _update_if_changed("reaction_type", normalized_exp.reaction_type, new_type)

    # Normalize list fields (strip whitespace, remove empties)
    def _normalize_list(items: list[str]) -> list[str]:
        return [item.strip() for item in items if item and item.strip()]

    _update_if_changed("reactants", normalized_exp.reactants, _normalize_list(normalized_exp.reactants))
    _update_if_changed("reagents", normalized_exp.reagents, _normalize_list(normalized_exp.reagents))
    _update_if_changed("products", normalized_exp.products, _normalize_list(normalized_exp.products))
    
    # Standardize catalyst naming (e.g., "palladium" -> "Pd")
    old_cats = normalized_exp.catalysts
    new_cats = _normalize_list(old_cats)
    
    cat_aliases = {
        "palladium": "Pd",
        "copper": "Cu",
        "nickel": "Ni",
        "ruthenium": "Ru",
        "iridium": "Ir",
    }
    
    final_cats = []
    for cat in new_cats:
        lower_cat = cat.lower()
        if lower_cat in cat_aliases:
            final_cats.append(cat_aliases[lower_cat])
        else:
            final_cats.append(cat)
            
    _update_if_changed("catalysts", old_cats, final_cats)

    # Normalize temperature bounds (cap at valid ranges just in case, or leave for validator)
    # The normalizer just cleans up raw data, the validator will check bounds.
    # Yield is already a float, but we can ensure it's not negative.
    if normalized_exp.yield_percent is not None and normalized_exp.yield_percent < 0:
        _update_if_changed("yield_percent", normalized_exp.yield_percent, 0.0)
        
    return normalized_exp, normalized_fields
