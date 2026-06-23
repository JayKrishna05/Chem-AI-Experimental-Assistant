import json
import argparse
import sys
import time
from pathlib import Path

from backend.providers import get_provider
from backend.planner.planner import Planner
import backend.planner.planner as planner_module

# Mock out _TOOL_DISPATCH to avoid DuckDB execution
from collections import defaultdict
planner_module._TOOL_DISPATCH = defaultdict(lambda: lambda **kwargs: {"status": "mocked"})

def run_benchmark(cases_path: str, model: str | None = None, output_path: str = "planner_failures.json"):
    print(f"Loading benchmark cases from {cases_path}")
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    provider = get_provider("ollama")
    planner = Planner(provider=provider, max_retries=1)

    print(f"Running benchmark across {len(cases)} cases using model={model or 'default'}...")
    
    passes = 0
    failures = []
    
    # Coverage tracking
    supported_total = 0
    partially_supported_total = 0
    unsupported_total = 0
    
    category_scores = defaultdict(lambda: {"total": 0, "pass": 0})

    for i, case in enumerate(cases):
        query = case["query"]
        expected_tool = case["expected_tool"]
        expected_filters = case.get("expected_filters", {})
        category = case["category"]
        classification = case["classification"]
        
        # Track coverage totals
        if classification == "Supported":
            supported_total += 1
        elif classification == "Partially Supported":
            partially_supported_total += 1
        elif classification == "Unsupported":
            unsupported_total += 1

        category_scores[category]["total"] += 1

        print(f"[{i+1}/{len(cases)}] {query} -> ", end="", flush=True)

        start_t = time.time()
        result = planner.plan(query, model=model, timeout=30.0)
        dur = time.time() - start_t

        actual_tool = result.tool if result.success else f"ERROR: {result.error}"
        actual_filters = result.filters

        # Check tool match
        tool_match = (actual_tool == expected_tool)
        
        # Check expected filters (only checking that expected keys match actual values, ignoring extra actual keys)
        filters_match = True
        for k, v in expected_filters.items():
            if actual_filters.get(k) != v:
                filters_match = False
                break

        passed = tool_match and filters_match

        if passed:
            print(f"PASS ({dur:.1f}s)")
            passes += 1
            category_scores[category]["pass"] += 1
        else:
            print(f"FAIL ({dur:.1f}s) - Expected: {expected_tool} {expected_filters}, Actual: {actual_tool} {actual_filters}")
            failures.append({
                "query": query,
                "expected_tool": expected_tool,
                "expected_filters": expected_filters,
                "actual_tool": actual_tool,
                "actual_filters": actual_filters,
                "raw_llm_response": result.raw_llm_response,
                "error": result.error,
                "category": category,
                "classification": classification
            })

    accuracy = (passes / len(cases)) * 100 if cases else 0
    coverage_score = ((supported_total + 0.5 * partially_supported_total) / len(cases)) * 100 if cases else 0

    print("\n" + "="*50)
    print(f"BENCHMARK RESULTS (Model: {model or 'default'})")
    print("="*50)
    print(f"Total Cases: {len(cases)}")
    print(f"Passes:      {passes}")
    print(f"Failures:    {len(failures)}")
    print(f"Accuracy:    {accuracy:.1f}%")
    print(f"Coverage:    {coverage_score:.1f}%")
    print("\nCategory Scores:")
    for cat, stats in category_scores.items():
        cat_acc = (stats["pass"] / stats["total"]) * 100
        print(f"  - {cat}: {stats['pass']}/{stats['total']} ({cat_acc:.1f}%)")
    print("="*50)

    if failures:
        out_file = output_path.replace(".json", f"_{model.replace(':', '_')}.json" if model else ".json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(failures, f, indent=2)
        print(f"Failures saved to {out_file}")

    return {
        "model": model,
        "accuracy": accuracy,
        "coverage": coverage_score,
        "failures": len(failures)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Planner Benchmark")
    parser.add_argument("--cases", type=str, default="tests/planner_benchmark_cases.json", help="Path to benchmark cases JSON")
    parser.add_argument("--models", type=str, nargs="+", help="Models to test (e.g. qwen2.5:3b tinyllama)")
    parser.add_argument("--output", type=str, default="planner_failures.json", help="Output path for failures")
    args = parser.parse_args()

    if args.models:
        results = []
        for m in args.models:
            print(f"\n--- Running benchmark for {m} ---")
            res = run_benchmark(args.cases, model=m, output_path=args.output)
            results.append(res)
        
        print("\n" + "="*50)
        print("LEADERBOARD")
        print("="*50)
        # Sort by accuracy descending
        results.sort(key=lambda x: x["accuracy"], reverse=True)
        for r in results:
            print(f"Model: {r['model']:<20} | Accuracy: {r['accuracy']:>5.1f}% | Failures: {r['failures']:>3}")
        print("="*50)
    else:
        run_benchmark(args.cases, output_path=args.output)
