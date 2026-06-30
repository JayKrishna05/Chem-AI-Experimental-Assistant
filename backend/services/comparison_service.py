"""Service layer for comparing CanonicalExperiments against the database."""

from __future__ import annotations
import time
from typing import Any

from backend.experiment.models import ValidationResult, ComparisonResult, EvidenceBundle
from backend.database.repositories.reaction_repository import ReactionRepository
from backend.database.repositories.statistics_repository import StatisticsRepository
from backend.tools.filters import CommonFilters


def compare_experiment(validation_result: ValidationResult) -> dict[str, Any]:
    """Compare a validated experiment against the DB using existing tools.
    
    Returns a Python dictionary representing the comparison report.
    """
    exp = validation_result.experiment
    start_time = time.time()
    
    report: dict[str, Any] = {
        "experiment_id": exp.experiment_id,
        "is_valid": validation_result.is_valid,
        "warnings": validation_result.warnings,
        "confidence_score": validation_result.confidence_score,
        "comparisons": {}
    }
    
    if not validation_result.is_valid:
        return report

    reaction_repo = ReactionRepository()
    stats_repo = StatisticsRepository()
    
    evidence = EvidenceBundle(
        matching_strategy="none",
        representative_reaction_ids=[],
        assumptions=[],
        query_filters={}
    )

    # 1. Similarity Search (Hierarchical matching)
    similar_matches = []
    total_matching = 0
    strategy = "none"
    
    reactants = exp.reactants or []
    products = exp.products or []
    catalysts = exp.catalysts or []
    
    # 1. reaction_type
    filters = CommonFilters()
    if exp.reaction_type:
        filters.reaction_type = exp.reaction_type
        similar_matches, total_matching = reaction_repo.search_reactions(filters, limit=5)
        if total_matching > 0:
            strategy = "reaction_type"

    # 2. Exact matching of all reactants + products
    if total_matching == 0 and reactants and products:
        similar_matches, total_matching = reaction_repo.search_by_components(
            reactants=reactants, products=products, limit=5
        )
        if total_matching > 0:
            strategy = "reactants_and_products"

    # 3. reactants only
    if total_matching == 0 and reactants:
        similar_matches, total_matching = reaction_repo.search_by_components(
            reactants=reactants, limit=5
        )
        if total_matching > 0:
            strategy = "reactants_only"

    # 4. products only
    if total_matching == 0 and products:
        similar_matches, total_matching = reaction_repo.search_by_components(
            products=products, limit=5
        )
        if total_matching > 0:
            strategy = "products_only"

    # 5. catalyst only
    if total_matching == 0 and catalysts:
        similar_matches, total_matching = reaction_repo.search_by_components(
            catalysts=catalysts, limit=5
        )
        if total_matching > 0:
            strategy = "catalyst_only"
            
    if similar_matches:
        evidence.representative_reaction_ids = [m["reaction_id"] for m in similar_matches]
        evidence.dataset_size = total_matching
        report["comparisons"]["similarity"] = {
            "strategy": strategy,
            "total_matches": total_matching,
            "top_matches": [m["reaction_id"] for m in similar_matches]
        }

    # Let's rebuild the logic. I will update this file again after enhancing the repositories if needed.
    # For now, let's just write the basic structure and fix the hierarchy.
    
    # 2. Optimal Conditions Comparison
    if strategy != "none":
        # Create an appropriate filter based on our successful strategy
        if strategy == "reaction_type":
            f = CommonFilters(reaction_type=exp.reaction_type)
        else:
            f = CommonFilters()
            if strategy in ["reactants_and_products", "reactants_only"]:
                f.reactant = reactants[0] if reactants else None
            elif strategy == "products_only":
                f.product = products[0] if products else None
            elif strategy == "catalyst_only":
                f.catalyst = catalysts[0] if catalysts else None

        optimal, freq = stats_repo.get_top_yield_conditions(f)
        if optimal:
            best = optimal[0]
            classification = "Comparable"
            
            # Use representative rationale strings
            rationale = "No yield reported to classify."
            
            if exp.yield_percent is not None and best.get("avg_yield") is not None:
                diff = best["avg_yield"] - exp.yield_percent
                stddev = best.get("stddev_yield") or 0.0
                
                if stddev > 0:
                    if diff <= (stddev * 0.5):
                        classification = "Excellent Match"
                        rationale = f"Yield ({exp.yield_percent}%) is within 0.5 standard deviations of the optimal dataset mean ({round(best['avg_yield'], 2)}%)."
                    elif diff <= stddev:
                        classification = "Comparable"
                        rationale = f"Yield ({exp.yield_percent}%) is within 1 standard deviation of the optimal dataset mean ({round(best['avg_yield'], 2)}%)."
                    elif diff <= (stddev * 2):
                        classification = "Slightly Below Optimal"
                        rationale = f"Yield ({exp.yield_percent}%) is more than 1 standard deviation below the optimal dataset mean ({round(best['avg_yield'], 2)}%)."
                    else:
                        classification = "Suboptimal"
                        rationale = f"Yield ({exp.yield_percent}%) is more than 2 standard deviations below the optimal dataset mean ({round(best['avg_yield'], 2)}%)."
                else:
                    if diff <= 5.0:
                        classification = "Excellent Match"
                        rationale = f"Yield ({exp.yield_percent}%) is very close to the optimal dataset mean ({round(best['avg_yield'], 2)}%)."
                    else:
                        classification = "Comparable"
                        rationale = f"Yield ({exp.yield_percent}%) compared to optimal dataset mean ({round(best['avg_yield'], 2)}%)."

            report["comparisons"]["optimal_conditions"] = {
                "matching_strategy": strategy,
                "best_catalyst": best.get("catalyst"),
                "best_avg_yield": best.get("avg_yield"),
                "user_yield": exp.yield_percent,
                "yield_classification": classification,
                "rationale": rationale
            }
            
            evidence.mean = best.get("avg_yield")
            evidence.standard_deviation = best.get("stddev_yield")
            evidence.sample_size = best.get("freq", 0)
            evidence.confidence_rationale = rationale

    # 3. Temperature Profiling
    if strategy != "none" and exp.temperature_c is not None:
        if strategy == "reaction_type":
            f = CommonFilters(reaction_type=exp.reaction_type)
        else:
            f = CommonFilters()
            if strategy in ["reactants_and_products", "reactants_only"]:
                f.reactant = reactants[0] if reactants else None
            elif strategy == "products_only":
                f.product = products[0] if products else None
            elif strategy == "catalyst_only":
                f.catalyst = catalysts[0] if catalysts else None
                
        temps = stats_repo.get_temperature_statistics(f)
        clean_stats = temps.get("clean_statistics")
        if clean_stats and clean_stats.get("average") is not None:
            avg_temp = clean_stats["average"]
            diff = exp.temperature_c - avg_temp
            report["comparisons"]["temperature_profile"] = {
                "user_temperature": exp.temperature_c,
                "db_average_temperature": round(avg_temp, 2),
                "difference": round(diff, 2),
                "is_anomalous": abs(diff) > 50  # More than 50C diff is an anomaly heuristic
            }
            evidence.assumptions.append("0°C values excluded from clean_statistics due to ORD placeholder prevalence.")

    evidence.matching_strategy = strategy
    evidence.execution_time_ms = (time.time() - start_time) * 1000
    
    report["evidence"] = evidence.model_dump()
    return report
