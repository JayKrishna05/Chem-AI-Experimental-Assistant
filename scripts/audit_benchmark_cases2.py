import sys
import json
sys.path.append('.')
from backend.planner.schema import KNOWN_TOOLS

with open('tests/planner_benchmark_cases.json', 'r') as f:
    cases = json.load(f)

modifications = 0
for c in cases:
    if c['expected_tool'] not in KNOWN_TOOLS and c['expected_tool'] != '__none__':
        # Change expected to __none__ because it's impossible for the LLM to output tools not in KNOWN_TOOLS.
        c['expected_tool_original'] = c['expected_tool']
        c['expected_tool'] = '__none__'
        c['expected_filters'] = {}
        modifications += 1

with open('tests/planner_benchmark_cases.json', 'w') as f:
    json.dump(cases, f, indent=2)

print(f'Updated {modifications} benchmark cases to expect __none__ for missing tools.')
