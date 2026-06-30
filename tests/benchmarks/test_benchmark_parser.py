import json
import time
import os
from backend.experiment.parser.parser_csv import parse_csv

csv_data = """reaction_type,reactants,products,temperature_c,yield_percent
Buchwald-Hartwig,"chlorobenzene; morpholine",4-phenylmorpholine,100,85.5
Suzuki,"phenylboronic acid, 1,2-dichloroethane",biphenyl,80,90
Amide Coupling,"[""acetic acid"", ""benzylamine""]",N-benzylacetamide,25,
Missing Temp,reactant A,product B,,50
Pipe separated,reactant A | reactant B,product C,0,20
"""

def run_benchmark():
    start = time.time()
    experiments = parse_csv(csv_data)
    duration = time.time() - start
    
    results = {
        "benchmark_name": "CSV Parser",
        "timestamp": time.time(),
        "execution_time_sec": duration,
        "total_parsed": len(experiments),
        "experiments": []
    }
    
    for exp in experiments:
        results["experiments"].append({
            "reaction_type": exp.reaction_type,
            "reactants": exp.reactants,
            "products": exp.products,
            "temperature_c": exp.temperature_c,
            "yield_percent": exp.yield_percent
        })
        
    os.makedirs("benchmarks/reports", exist_ok=True)
    with open("benchmarks/reports/parser_baseline.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Parser benchmark complete. Total parsed: {len(experiments)}. Execution time: {duration:.4f}s")

if __name__ == "__main__":
    run_benchmark()
