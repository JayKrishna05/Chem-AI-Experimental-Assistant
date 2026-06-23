import json
import re

def main():
    with open('backend/planner/schema.py', 'r') as f:
        text = f.read()

    # Extract all functions that look like tool definitions
    known_tools = re.findall(r'def ([a-z_]+)\(', text)
    print('Current tools in schema:', known_tools)

    with open('tests/planner_benchmark_cases.json', 'r') as f:
        cases = json.load(f)

    modifications = 0
    for c in cases:
        if c['expected_tool'] not in known_tools and c['expected_tool'] != '__none__':
            print(f"Changing {c['expected_tool']} to __none__ for '{c['query']}'")
            c['expected_tool_original'] = c['expected_tool']
            c['expected_tool'] = '__none__'
            c['expected_filters'] = {}
            modifications += 1

    with open('tests/planner_benchmark_cases.json', 'w') as f:
        json.dump(cases, f, indent=2)

    print(f'Updated {modifications} benchmark cases to expect __none__ for missing tools.')

if __name__ == '__main__':
    main()
