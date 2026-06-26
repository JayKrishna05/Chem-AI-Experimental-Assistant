"""Service layer for comparing CanonicalExperiments against the database."""

from __future__ import annotations

from typing import Any

from backend.experiment.models import ValidationResult
from backend.tools.analytics_tools import temperature_statistics, top_yield_conditions
from backend.tools.chemistry_tools import search_reactions


def compare_experiment(validation_result: ValidationResult) -> dict[str, Any]:
    """Compare a validated experiment against the DB using existing tools.
    
    Returns a Python dictionary representing the comparison report.
    """
    exp = validation_result.experiment
    report: dict[str, Any] = {
        "experiment_id": exp.experiment_id,
        "is_valid": validation_result.is_valid,
        "warnings": validation_result.warnings,
        "confidence_score": validation_result.confidence_score,
        "comparisons": {}
    }
    
    if not validation_result.is_valid:
        return report

    # 1. Similarity Search (Find identical reactions by reactants/products)
    if exp.reactants and exp.products:
        # Just use the first reactant and product for the heuristic search
        res = search_reactions(
            reactant=exp.reactants[0],
            product=exp.products[0],
            limit=5
        )
        report["comparisons"]["similar_reactions"] = {
            "total_matching": res.get("total_matching_rows", 0),
            "top_matches": [
                {"reaction_id": r.get("reaction_id"), "reaction_type": r.get("reaction_type")} 
                for r in res.get("results", [])
            ]
        }

    # 2. Optimal Conditions Comparison
    if exp.reaction_type:
        optimal = top_yield_conditions(reaction_type=exp.reaction_type)
        if optimal.get("results"):
            best = optimal["results"][0]
            classification = "Comparable"
            if exp.yield_percent is not None and best.get("avg_yield") is not None:
                diff = best["avg_yield"] - exp.yield_percent
                if diff <= 1.0:
                    classification = "Excellent Match"
                elif 1.0 < diff <= 5.0:
                    classification = "Comparable"
                elif 5.0 < diff <= 10.0:
                    classification = "Slightly Below Optimal"
                else:
                    classification = "Suboptimal"

            report["comparisons"]["optimal_conditions"] = {
                "reaction_type": exp.reaction_type,
                "best_catalyst": best.get("catalyst"),
                "best_avg_yield": best.get("avg_yield"),
                "user_yield": exp.yield_percent,
                "yield_classification": classification
            }

    # 3. Temperature Profiling
    if exp.reaction_type and exp.temperature_c is not None:
        temps = temperature_statistics(reaction_type=exp.reaction_type)
        if temps.get("results") and temps["results"]:
            clean_stats = temps["results"][0].get("clean_statistics")
            if clean_stats and clean_stats.get("average") is not None:
                avg_temp = clean_stats["average"]
                diff = exp.temperature_c - avg_temp
                report["comparisons"]["temperature_profile"] = {
                    "user_temperature": exp.temperature_c,
                    "db_average_temperature": round(avg_temp, 2),
                    "difference": round(diff, 2),
                    "is_anomalous": abs(diff) > 50  # More than 50C diff is an anomaly heuristic
                }

    return report
