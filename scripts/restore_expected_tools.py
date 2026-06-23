import sys
import json
sys.path.append('.')
from backend.planner.schema import KNOWN_TOOLS

with open('tests/planner_benchmark_cases.json', 'r') as f:
    cases = json.load(f)

modifications = 0
for c in cases:
    if 'expected_tool_original' in c:
        orig = c['expected_tool_original']
        if orig in KNOWN_TOOLS:
            print(f"Restoring {orig} for '{c['query']}'")
            c['expected_tool'] = orig
            # We don't restore filters perfectly here if we wiped them out, but we can just leave them as {} for now 
            # since most of these didn't have filters anyway, OR we can regenerate the json from scratch!
            modifications += 1

with open('tests/planner_benchmark_cases.json', 'w') as f:
    json.dump(cases, f, indent=2)

print(f'Restored {modifications} benchmark cases.')
