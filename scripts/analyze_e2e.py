import json
import statistics

with open('tests/e2e_benchmark_results.json') as f:
    data = json.load(f)

planner_lats = [d['planner_latency'] for d in data]
tool_lats = [d['tool_latency'] for d in data]
formatter_lats = [d['formatter_latency'] for d in data]
e2e_lats = [d['e2e_latency'] for d in data]

def print_stats(name, lats):
    print(f'{name} Latency:')
    print(f'  Mean: {statistics.mean(lats):.2f}s')
    print(f'  Median (p50): {statistics.median(lats):.2f}s')
    try:
        print(f'  p95: {statistics.quantiles(lats, n=20)[18]:.2f}s')
    except:
        pass
    print(f'  Max: {max(lats):.2f}s')

print(f'Total Executions: {len(data)}')
print_stats('Planner', planner_lats)
print_stats('Tool', tool_lats)
print_stats('Formatter', formatter_lats)
print_stats('End-to-End', e2e_lats)

print('\nQualitative Check - 10 cases:')
for d in data[:5]:
    print(f"Q: {d['query']}")
    print(f"A: {d['final_response'][:100]}...\n")
