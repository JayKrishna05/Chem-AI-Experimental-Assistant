"""
Comprehensive Planner + Tool Audit
Tests 70 queries and records pass/fail with notes.
"""
import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000"

def post_chat(message: str):
    data = {"message": message}
    req = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    events = []
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            for line in resp:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith("data: "):
                    events.append(json.loads(line_str[6:]))
    except Exception as e:
        return {"error": str(e), "events": events}
    return events

def check(events):
    """Return dict of outcome analysis."""
    if isinstance(events, dict):
        return {"outcome": "ERROR", "detail": events.get("error")}
    types = [e.get("type") for e in events]
    if "error" in types:
        err_ev = next(e for e in events if e.get("type") == "error")
        return {"outcome": "ERROR", "detail": err_ev.get("message")}
    if "no_tool" in types:
        return {"outcome": "NO_TOOL", "detail": None}
    if "tool_result" in types:
        tr = next(e for e in events if e.get("type") == "tool_result")
        tool_sel = next((e for e in events if e.get("type") == "tool_selected"), None)
        return {
            "outcome": "TOOL_RESULT",
            "tool": tool_sel.get("tool") if tool_sel else None,
            "filters": tool_sel.get("filters") if tool_sel else None,
            "result_count": tr.get("result", {}).get("count"),
            "text": (tr.get("text") or "")[:120],
        }
    return {"outcome": "UNKNOWN", "types": types}

TESTS = [
    # Category A - Database Summary
    (1,  "Summarize the database",                                   "tool_result", "dataset_summary"),
    (2,  "How many reactions exist?",                                "tool_result", "dataset_summary"),
    (3,  "How many procedures exist?",                               "tool_result", "dataset_summary"),
    (4,  "How many molecules exist?",                                "tool_result", "dataset_summary"),
    (5,  "How many source datasets exist?",                          "tool_result", "dataset_summary"),
    # Category B - Reaction Types
    (6,  "What reaction types are available?",                       "tool_result", "reaction_type_statistics"),
    (7,  "Which reaction type is most common?",                      "tool_result", "reaction_type_statistics"),
    (8,  "Which reaction type has the most procedures?",             "tool_result", "reaction_type_statistics"),
    (9,  "Which reaction type has the most yield information?",      "tool_result", "reaction_type_statistics"),
    (10, "Which reaction type has the most temperature information?","tool_result", "reaction_type_statistics"),
    # Category C - Source Datasets
    (11, "Which datasets contain the most reactions?",               "tool_result", "source_dataset_statistics"),
    (12, "Which datasets contain the most procedures?",              "tool_result", "source_dataset_statistics"),
    (13, "Which datasets contain the most yield data?",              "tool_result", "source_dataset_statistics"),
    (14, "Which datasets contain the most temperature data?",        "tool_result", "source_dataset_statistics"),
    (15, "Compare dataset coverage",                                 "tool_result", "source_dataset_statistics"),
    # Category D - Catalyst Analytics
    (16, "Show catalyst statistics",                                 "tool_result", "catalyst_statistics"),
    (17, "Most common catalysts",                                    "tool_result", "catalyst_statistics"),
    (18, "Most common catalysts in Buchwald-Hartwig reactions",      "tool_result", "catalyst_statistics"),
    (19, "Most common catalysts in Suzuki reactions",                "tool_result", "catalyst_statistics"),
    (20, "Most common catalysts in amide coupling reactions",        "tool_result", "catalyst_statistics"),
    (21, "Which catalysts appear most often overall?",               "tool_result", "catalyst_statistics"),
    (22, "Which catalysts contain palladium?",                       "tool_result", None),  # any tool
    (23, "Which catalysts contain copper?",                          "tool_result", None),
    (24, "Which catalysts contain iron?",                            "tool_result", None),
    (25, "Which reaction types use palladium catalysts most often?", "tool_result", None),
    # Category E - Temperature
    (26, "Show temperature statistics",                              "tool_result", "temperature_statistics"),
    (27, "Average temperature",                                      "tool_result", "temperature_statistics"),
    (28, "Median temperature",                                       "tool_result", "temperature_statistics"),
    (29, "Temperature distribution",                                 "tool_result", "temperature_statistics"),
    (30, "Which reaction type has the highest temperatures?",        "tool_result", "temperature_statistics"),
    (31, "Which dataset has the highest temperatures?",              "tool_result", "temperature_statistics"),
    # Category F - Yield
    (32, "Show yield statistics",                                    "tool_result", "yield_statistics"),
    (33, "Average yield",                                            "tool_result", "yield_statistics"),
    (34, "Median yield",                                             "tool_result", "yield_statistics"),
    (35, "Yield distribution",                                       "tool_result", "yield_statistics"),
    (36, "Which reaction type has the highest average yield?",       "tool_result", "yield_statistics"),
    (37, "Which dataset has the highest average yield?",             "tool_result", "yield_statistics"),
    # Category G - Procedure Search
    (38, "Show procedures mentioning palladium",                     "tool_result", "search_procedures"),
    (39, "Show procedures mentioning copper",                        "tool_result", "search_procedures"),
    (40, "Show procedures mentioning chromatography",                "tool_result", "search_procedures"),
    (41, "Show procedures mentioning ethanol",                       "tool_result", "search_procedures"),
    (42, "Show procedures mentioning reflux",                        "tool_result", "search_procedures"),
    # Category H - Reaction Search
    (43, "Find Buchwald-Hartwig reactions",                          "tool_result", "search_reactions"),
    (44, "Find Suzuki reactions",                                    "tool_result", "search_reactions"),
    (45, "Find amide coupling reactions",                            "tool_result", "search_reactions"),
    (46, "Find reactions containing palladium catalysts",            "tool_result", "search_reactions"),
    (47, "Find reactions containing copper catalysts",               "tool_result", "search_reactions"),
    (48, "Find reactions involving boronic acids",                   "tool_result", "search_reactions"),
    # Category I - Molecule Search
    (49, "Find ethanol",                                             "tool_result", "molecule_lookup"),
    (50, "Find acetone",                                             "tool_result", "molecule_lookup"),
    (51, "Find caffeine",                                            "tool_result", "molecule_lookup"),
    (52, "Find aspirin",                                             "tool_result", "molecule_lookup"),
    (53, "Find benzene-containing molecules",                        "tool_result", "molecule_lookup"),
    # Category J - Comparison
    (54, "Compare Buchwald-Hartwig and Suzuki reactions",            "tool_result", None),
    (55, "Compare catalyst usage between reaction types",            "tool_result", None),
    (56, "Compare dataset coverage",                                 "tool_result", None),
    (57, "Compare temperature distributions",                        "tool_result", None),
    (58, "Compare yield distributions",                              "tool_result", None),
    # Category K - Natural Language
    (59, "What catalysts are commonly used for Buchwald-Hartwig chemistry?", "tool_result", "catalyst_statistics"),
    (60, "Which reaction types have the best yields?",               "tool_result", "reaction_type_statistics"),
    (61, "Which datasets are richest in experimental data?",         "tool_result", "source_dataset_statistics"),
    (62, "What chemistry is best represented in the database?",      "tool_result", None),
    # Category L - Edge Cases
    (63, "What is the capital of France?",                           "no_tool",     None),
    (64, "Tell me a joke.",                                          "no_tool",     None),
    (65, "Write a Python quicksort.",                                "no_tool",     None),
    (66, "Explain quantum mechanics.",                               "no_tool",     None),
    (67, "asdfqwer zxcvjklm",                                       "no_tool",     None),
    (68, "What reaction types have data? " * 50,                     "tool_result", None),
    (70, "reactions",                                                "tool_result", None),
]

results = []
for i, (num, question, expected_outcome, expected_tool) in enumerate(TESTS):
    print(f"[{num:2d}] {question[:60]:<60}", end=" ", flush=True)
    events = post_chat(question)
    outcome = check(events)

    actual_outcome = outcome["outcome"]
    actual_tool = outcome.get("tool")

    # Pass/fail logic
    if expected_outcome == "tool_result":
        passed = actual_outcome == "TOOL_RESULT"
        if expected_tool and passed:
            tool_match = actual_tool == expected_tool
        else:
            tool_match = True  # any tool accepted
    elif expected_outcome == "no_tool":
        passed = actual_outcome == "NO_TOOL"
        tool_match = True
    else:
        passed = True
        tool_match = True

    status = "PASS" if (passed and tool_match) else "FAIL"
    results.append((num, question, expected_outcome, expected_tool, status, actual_outcome, actual_tool, outcome))
    print(f"{status}  outcome={actual_outcome} tool={actual_tool}")
    sys.stdout.flush()

print()
print("=" * 70)
print("SUMMARY")
passes = sum(1 for r in results if r[4] == "PASS")
fails = sum(1 for r in results if r[4] == "FAIL")
print(f"PASS: {passes}  FAIL: {fails}  TOTAL: {len(results)}")
print()
print("FAILURES:")
for r in results:
    if r[4] == "FAIL":
        print(f"  [{r[0]:2d}] {r[1][:50]} | expected={r[2]}/{r[3]} | got={r[5]}/{r[6]}")
        if r[7].get("detail"):
            print(f"       detail: {r[7]['detail'][:100]}")
