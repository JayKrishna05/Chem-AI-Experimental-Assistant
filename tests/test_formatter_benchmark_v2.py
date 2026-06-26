import json
import time
import os
from dotenv import load_dotenv
from backend.chat.formatter import format_response
from backend.planner.planner import PlannerResult
from backend.providers.provider_factory import get_provider

load_dotenv()

def run_benchmark():
    provider = get_provider("groq")
    model = "llama-3.3-70b-versatile"
    
    with open("tests/formatter_benchmark_cases_v2.json", "r") as f:
        cases = json.load(f)
        
    results = []
    total_time = 0
    
    for idx, case in enumerate(cases):
        print(f"Testing {case['id']}...")
        pr = PlannerResult(
            success=True,
            question=case["question"],
            tool=case["tool"],
            tool_result=case["tool_result"],
        )
        
        start = time.perf_counter()
        response_text = format_response(provider, pr, model=model)
        duration = time.perf_counter() - start
        
        total_time += duration
        
        # We can't strictly get tokens from format_response right now since it just returns a string,
        # but we can track length and time.
        results.append({
            "id": case["id"],
            "duration_s": duration,
            "response_length": len(response_text),
            "response": response_text
        })
        time.sleep(1) # rate limit protection
        
    with open("tests/formatter_benchmark_v2_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Finished {len(cases)} cases in {total_time:.2f}s")

if __name__ == "__main__":
    run_benchmark()
