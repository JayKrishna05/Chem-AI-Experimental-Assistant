import json
import os
import concurrent.futures
import time
from backend.providers import get_provider
from backend.providers.base import Message
from typing import List, Dict, Any

PROMPT_A = (
    "You are an expert chemistry AI assistant. "
    "A user asked a question, and a backend tool was executed to answer it. "
    "Your task is to summarize the raw JSON output into a natural, conversational response. "
    "Focus on the most important numbers, findings, or trends. "
    "If the tool found zero results or no data, state that clearly. "
    "Do not invent information or mention the underlying JSON structure. "
    "IMPORTANT: If the JSON contains both 'statistics' and 'clean_statistics', "
    "prefer 'clean_statistics' as it filters out extreme outliers and uses chemically "
    "meaningful ranges (yields 0-100%, temperatures -100°C to 300°C). "
    "If clean_statistics has far fewer records than the total, mention the data quality issue. "
    "Always report average, median, min, and max from clean_statistics when available."
)

PROMPT_B = (
    "You are a strict, highly analytical Data Reviewer for a chemistry database. A user asked a question, and a backend tool was executed. The raw JSON output of that tool is provided to you. \n"
    "Your sole responsibility is to translate the JSON into a structured, evidence-based report. \n"
    "You MUST follow these strict rules:\n"
    "### RULE 1: Evidence First\n"
    "You may only report data that is explicitly present in the JSON. Do not invent context, and do not reference external chemical knowledge unless interpreting the explicit results. Do NOT use conversational padding.\n"
    "### RULE 2: No Statistical Hallucination\n"
    "You are STRICTLY BANNED from computing averages, medians, percentages, or distributions yourself. \n"
    "- If the JSON contains an array of results but no `statistics` block, DO NOT average the results yourself. Just list them.\n"
    "- If the JSON provides `clean_statistics`, use ONLY those values.\n"
    "### RULE 3: Truncation Awareness\n"
    "Look closely at the data. \n"
    "- If there is a `count` or `total_records` field that is larger than the number of items in the `results` array, or if a `_note` mentions truncation, you MUST explicitly state: \"Warning: Data is truncated. Only showing a partial sample.\"\n"
    "- If data is truncated, DO NOT infer general trends from the visible sample.\n"
    "### RULE 4: Data Quality Detection\n"
    "Flag any of the following if you see them in the raw data:\n"
    "- Yields > 100% or < 0%\n"
    "- Temperatures < -273°C\n"
    "- Widespread missing fields (e.g. `reaction_type = null`)\n"
    "- If `clean_statistics` has a drastically lower `records_with_finite_value` than `total_records`.\n"
    "### RULE 5: Output Structure\n"
    "You MUST format your entire response using exactly this markdown structure, omitting sections that do not apply:\n"
    "**Observations:**\n"
    "[Bullet points stating strictly what the data shows]\n\n"
    "**Data Quality Notes:**\n"
    "[Any truncation warnings, impossible values, or missing data flags. If none, write \"None.\"]\n\n"
    "**Interpretation:**\n"
    "[Brief answer to the user's question based strictly on the observations above]\n\n"
    "**Confidence:**\n"
    "[HIGH (Complete statistical data) / MEDIUM (Clear trends but missing data) / LOW (Truncated list or small sample)]"
)

def evaluate_case(provider, case, prompt_text: str, model="llama-3.3-70b-versatile"):
    user_content = (
        f"Question: {case['query']}\n\n"
        f"Tool Used: {case['tool_name']}\n\n"
        f"Raw Output:\n{json.dumps(case['tool_output'], indent=2)}"
    )
    messages = [
        Message(role="system", content=prompt_text),
        Message(role="user", content=user_content),
    ]
    try:
        response = provider.chat(messages, model=model, timeout=30.0)
        return response.content
    except Exception as e:
        return f"ERROR: {e}"

def main():
    print("Loading cases...")
    with open('tests/formatter_ab_test_cases.json', 'r') as f:
        cases = json.load(f)
        
    provider = get_provider("groq")
    
    results = []
    
    # We will score them manually/heuristically here for the report
    for case in cases:
        print(f"Testing {case['id']}...")
        ans_a = evaluate_case(provider, case, PROMPT_A)
        ans_b = evaluate_case(provider, case, PROMPT_B)
        
        results.append({
            "id": case["id"],
            "query": case["query"],
            "ans_a": ans_a,
            "ans_b": ans_b
        })
        time.sleep(1) # rate limit protection

    with open('tests/formatter_ab_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    print("Saved to tests/formatter_ab_test_results.json")

if __name__ == "__main__":
    main()
