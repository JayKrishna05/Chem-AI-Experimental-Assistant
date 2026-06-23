import json
import traceback

with open('planner_failures_qwen2.5_3b.json', 'r', encoding='utf-8') as f:
    failures = json.load(f)

genuine_failures = []
false_failures = 0

for fail in failures:
    ex_tool = fail['expected_tool']
    ac_tool = fail['actual_tool']
    ex_filt = fail['expected_filters']
    ac_filt = fail['actual_filters']
    
    # 1. Expected tool and actual tool identical
    # Check if filters are identical OR if they differ only by query vs smiles
    if ex_tool == ac_tool:
        # Are they identical?
        if ex_filt == ac_filt:
            false_failures += 1
            continue
            
        # Do they differ only by query vs smiles but values match?
        ex_keys = set(ex_filt.keys())
        ac_keys = set(ac_filt.keys())
        
        # If the values are identical, and keys are identical except query/smiles swap
        ex_vals = set(str(v) for v in ex_filt.values())
        ac_vals = set(str(v) for v in ac_filt.values())
        
        if ex_vals == ac_vals:
            # We assume it's just a key swap
            false_failures += 1
            continue
            
    genuine_failures.append(fail)

# Calculate stats
total_cases = 100
raw_failures = len(failures)
raw_passes = total_cases - raw_failures
raw_accuracy = raw_passes / total_cases * 100

corrected_passes = raw_passes + false_failures
corrected_accuracy = corrected_passes / total_cases * 100

with open('genuine_failures.json', 'w', encoding='utf-8') as f:
    json.dump(genuine_failures, f, indent=2)

print(f"Raw accuracy: {raw_accuracy:.1f}%")
print(f"Corrected accuracy: {corrected_accuracy:.1f}%")
print(f"False failures: {false_failures}")

# Let's count missing tool frequencies from genuine failures
missing_tools = {}
for fail in genuine_failures:
    ex = fail['expected_tool']
    if fail['classification'] == 'Unsupported' or fail['classification'] == 'Partially Supported':
        missing_tools[ex] = missing_tools.get(ex, 0) + 1

print("\nMissing tool counts:")
for k, v in sorted(missing_tools.items(), key=lambda item: item[1], reverse=True):
    print(f"{k}: {v}")
