import json
import time
import os
from backend.experiment.models import CanonicalExperiment, ValidationResult
from backend.services.comparison_service import compare_experiment

experiments_to_test = [
    CanonicalExperiment(
        reaction_type="Buchwald-Hartwig",
        reactants=["chlorobenzene", "morpholine"],
        products=["4-phenylmorpholine"],
        temperature_c=100.0,
        yield_percent=85.0
    ),
    CanonicalExperiment(
        reaction_type="Suzuki",
        reactants=["phenylboronic acid", "4-bromotoluene"],
        products=["4-methylbiphenyl"],
        temperature_c=80.0,
        yield_percent=90.0
    ),
    CanonicalExperiment(
        reaction_type=None,
        reactants=["aniline", "acetic anhydride"],
        products=["acetanilide"],
        temperature_c=25.0,
        yield_percent=95.0
    )
]

def run_benchmark():
    results = {
        "benchmark_name": "Comparison Engine",
        "timestamp": time.time(),
        "total_experiments": len(experiments_to_test),
        "results": []
    }
    
    start = time.time()
    for exp in experiments_to_test:
        val_result = ValidationResult(experiment=exp)
        
        t0 = time.time()
        comp_report = compare_experiment(val_result)
        t1 = time.time()
        
        results["results"].append({
            "experiment_id": exp.experiment_id,
            "reaction_type": exp.reaction_type,
            "execution_time_sec": t1 - t0,
            "report": comp_report
        })
        
    duration = time.time() - start
    results["total_execution_time_sec"] = duration
    
    os.makedirs("benchmarks/reports", exist_ok=True)
    with open("benchmarks/reports/comparison_baseline.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Comparison benchmark complete. Total execution time: {duration:.4f}s")

if __name__ == "__main__":
    run_benchmark()
