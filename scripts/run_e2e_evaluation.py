import json
import time
import os
from dotenv import load_dotenv

from backend.providers.provider_factory import get_provider
from backend.planner.planner import Planner, _TOOL_DISPATCH
from backend.chat.formatter import format_response

load_dotenv()

def run_e2e_benchmark():
    planner_provider = get_provider("ollama")
    ollama_provider = get_provider("ollama")
    groq_provider = get_provider("groq")
    planner = Planner(ollama_provider)
    planner_model = "qwen2.5:3b"
    formatter_model_groq = "llama-3.1-8b-instant"
    formatter_model_ollama = "qwen2.5:3b"
    
    with open("tests/e2e_queries.json", "r") as f:
        queries = json.load(f)
        
    ITERATIONS = 5  # 20 queries * 5 = 100 total executions
    
    results = []
    
    print(f"Running E2E Evaluation: {len(queries)} queries * {ITERATIONS} iterations = {len(queries) * ITERATIONS} total executions.")
    
    for iteration in range(ITERATIONS):
        print(f"--- Iteration {iteration + 1} ---")
        for query in queries:
            print(f"Query: {query}")
            
            # 1. Planner Latency
            start_e2e = time.perf_counter()
            start_planner = time.perf_counter()
            plan_result = planner.plan(query, model=planner_model)
            planner_latency = time.perf_counter() - start_planner
            
            # 2. Tool Latency
            tool_latency = 0.0
            if plan_result.success and not plan_result.is_no_tool():
                tool_func = _TOOL_DISPATCH.get(plan_result.tool)
                if tool_func:
                    start_tool = time.perf_counter()
                    try:
                        plan_result.tool_result = tool_func(**plan_result.filters)
                    except Exception as e:
                        plan_result.tool_result = {"error": str(e)}
                    tool_latency = time.perf_counter() - start_tool
            
            # 3. Formatter Latency
            start_formatter = time.perf_counter()
            response_text = ""
            
            f_prov = groq_provider if iteration == 0 else ollama_provider
            f_mod = formatter_model_groq if iteration == 0 else formatter_model_ollama
            
            for attempt in range(5):
                try:
                    response_text = format_response(f_prov, plan_result, model=f_mod)
                    break
                except Exception as e:
                    if "Rate limit reached" in str(e) or "429" in str(e):
                        print(f"Rate limit hit, sleeping 15s... (Attempt {attempt+1})")
                        time.sleep(15)
                        response_text = f"Error: {e}"
                    else:
                        response_text = f"Error: {e}"
                        break
            
            formatter_latency = time.perf_counter() - start_formatter
            
            e2e_latency = time.perf_counter() - start_e2e
            
            results.append({
                "iteration": iteration + 1,
                "query": query,
                "plan_tool": plan_result.tool,
                "plan_filters": plan_result.filters,
                "planner_latency": planner_latency,
                "tool_latency": tool_latency,
                "formatter_latency": formatter_latency,
                "e2e_latency": e2e_latency,
                "final_response": response_text
            })
            
            # Write incrementally
            with open("tests/e2e_benchmark_results.json", "w") as f:
                json.dump(results, f, indent=2)
                
            time.sleep(0.5) # rate limit protection
            
    print("Saved to tests/e2e_benchmark_results.json")

if __name__ == "__main__":
    run_e2e_benchmark()
