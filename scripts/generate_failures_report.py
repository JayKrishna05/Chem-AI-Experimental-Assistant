import json
from collections import defaultdict

with open('planner_failures_qwen2.5_3b.json', 'r') as f:
    failures = json.load(f)

categories = defaultdict(list)
for f in failures:
    expected_tool = f.get('expected_tool', '')
    actual_tool = f.get('actual_tool', '')
    
    cat = ""
    if expected_tool == '__none__':
        cat = "Unsupported Workflow / Missing Tool"
    elif expected_tool == actual_tool:
        cat = "Filter Selection Error"
    else:
        cat = "Planner Routing Error"
    categories[cat].append(f)

difficulty = {
    "Unsupported Workflow / Missing Tool": "High (Requires Phase 5)",
    "Filter Selection Error": "Medium (Prompt/Schema Tuning)",
    "Planner Routing Error": "Low (Few-shot Examples)"
}

gain = {
    "Unsupported Workflow / Missing Tool": f"{len(categories['Unsupported Workflow / Missing Tool'])}%",
    "Filter Selection Error": f"{len(categories['Filter Selection Error'])}%",
    "Planner Routing Error": f"{len(categories['Planner Routing Error'])}%"
}

with open('remaining_failures_report.md', 'w') as out:
    out.write("# Remaining Failures Analysis\n\n")
    out.write(f"**Total Remaining Failures:** {len(failures)} (representing the 42% accuracy gap)\n\n")
    
    out.write("## 1. Summary Table\n\n")
    out.write("| Failure Cause | Count | Difficulty | Expected Gain |\n")
    out.write("| ------------- | ----- | ---------- | ------------- |\n")
    for cat in ["Unsupported Workflow / Missing Tool", "Filter Selection Error", "Planner Routing Error"]:
        count = len(categories[cat])
        out.write(f"| {cat} | {count} | {difficulty[cat]} | {gain[cat]} |\n")
    
    out.write("\n## 2. Detailed Breakdown\n\n")
    for cat in ["Unsupported Workflow / Missing Tool", "Filter Selection Error", "Planner Routing Error"]:
        items = categories[cat]
        out.write(f"### {cat}\n")
        out.write(f"- **Failure count:** {len(items)}\n")
        out.write(f"- **Percentage:** {len(items)/len(failures)*100:.1f}%\n")
        out.write(f"- **Estimated Implementation Effort:** {difficulty[cat]}\n")
        out.write(f"- **Estimated Benchmark Gain:** {gain[cat]}\n\n")
        out.write("**Representative Examples:**\n")
        for f in items[:3]:
            out.write(f"- **Query:** `{f['query']}`\n")
            out.write(f"  - Expected: `{f['expected_tool']}` (Filters: `{f['expected_filters']}`)\n")
            out.write(f"  - Actual: `{f['actual_tool']}` (Filters: `{f.get('actual_filters', {})}`)\n")
        out.write("\n")

print("Generated remaining_failures_report.md")
