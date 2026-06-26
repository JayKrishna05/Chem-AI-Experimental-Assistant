"""
Comprehensive Capability Audit Tests
Tests all categories of the 100-question audit.
Run with: python scripts/test_audit.py
Requires: API running at localhost:8000
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8000"


def post_chat(message: str, timeout: int = 90) -> list[dict]:
    """Post a chat message and return all SSE events."""
    req = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=json.dumps({"message": message}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    events = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    events.append(json.loads(line_str[6:]))
    except Exception as e:
        return [{"type": "error", "message": str(e)}]
    return events


def get_event(events: list[dict], event_type: str) -> dict | None:
    return next((e for e in events if e.get("type") == event_type), None)


def has_type(events: list[dict], event_type: str) -> bool:
    return any(e.get("type") == event_type for e in events)


def assert_tool_result(events: list[dict], expected_tool: str | None = None) -> dict:
    """Assert tool_result is present and optionally check tool name."""
    tr = get_event(events, "tool_result")
    assert tr is not None, f"Expected tool_result, got: {[e.get('type') for e in events]}"
    if expected_tool:
        ts = get_event(events, "tool_selected")
        assert ts is not None, "Expected tool_selected event"
        actual = ts.get("tool")
        assert actual == expected_tool, f"Expected tool={expected_tool!r}, got {actual!r}"
    return tr


def assert_no_tool(events: list[dict]) -> None:
    assert has_type(events, "no_tool"), f"Expected no_tool, got: {[e.get('type') for e in events]}"


def check_result_nonempty(tr: dict) -> None:
    result = tr.get("result", {})
    count = result.get("count", -1)
    results = result.get("results", [])
    assert count != 0 or len(results) > 0 or "counts" in result or "statistics" in result, \
        f"Expected non-empty result, got count={count}"


PASS = 0
FAIL = 0


def run(name: str, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  PASS  {name}")
        PASS += 1
    except AssertionError as e:
        print(f"  FAIL  {name}: {e}")
        FAIL += 1
    except Exception as e:
        print(f"  FAIL  {name}: {type(e).__name__}: {e}")
        FAIL += 1


# ===== CATEGORY A: DATABASE SUMMARY =====

def test_a1_summarize():
    tr = assert_tool_result(post_chat("Summarize the database"), "dataset_summary")
    assert "counts" in tr["result"]

def test_a2_reaction_count():
    tr = assert_tool_result(post_chat("How many reactions exist?"), "dataset_summary")
    c = tr["result"]["counts"]
    assert c["reaction_count"] == 2376120, f"Expected 2376120, got {c['reaction_count']}"

def test_a3_procedure_count():
    tr = assert_tool_result(post_chat("How many procedures exist?"), "dataset_summary")
    c = tr["result"]["counts"]
    assert c["procedure_count"] == 1788170

def test_a4_molecule_count():
    tr = assert_tool_result(post_chat("How many molecules exist?"), "dataset_summary")
    c = tr["result"]["counts"]
    assert c["molecule_count"] == 1993180

def test_a5_dataset_count():
    tr = assert_tool_result(post_chat("How many source datasets exist?"), "dataset_summary")
    c = tr["result"]["counts"]
    assert c["source_dataset_count"] == 542

# ===== CATEGORY B: REACTION TYPES =====

def test_b6_reaction_types():
    tr = assert_tool_result(post_chat("What reaction types are available?"), "reaction_type_statistics")
    check_result_nonempty(tr)

def test_b7_most_common_type():
    tr = assert_tool_result(post_chat("Which reaction type is most common?"), "reaction_type_statistics")
    check_result_nonempty(tr)

def test_b8_most_procedures():
    tr = assert_tool_result(post_chat("Which reaction type has the most procedures?"), "reaction_type_statistics")
    check_result_nonempty(tr)

def test_b9_most_yield():
    tr = assert_tool_result(post_chat("Which reaction type has the most yield information?"), "reaction_type_statistics")
    check_result_nonempty(tr)

def test_b10_most_temp():
    tr = assert_tool_result(post_chat("Which reaction type has the most temperature information?"), "reaction_type_statistics")
    check_result_nonempty(tr)

# ===== CATEGORY C: SOURCE DATASETS =====

def test_c11_most_reactions():
    tr = assert_tool_result(post_chat("Which datasets contain the most reactions?"), "source_dataset_statistics")
    check_result_nonempty(tr)

def test_c12_most_procedures():
    tr = assert_tool_result(post_chat("Which datasets contain the most procedures?"), "source_dataset_statistics")
    check_result_nonempty(tr)

def test_c13_most_yield():
    tr = assert_tool_result(post_chat("Which datasets contain the most yield data?"), "source_dataset_statistics")
    check_result_nonempty(tr)

def test_c14_most_temp():
    tr = assert_tool_result(post_chat("Which datasets contain the most temperature data?"), "source_dataset_statistics")
    check_result_nonempty(tr)

def test_c15_compare():
    tr = assert_tool_result(post_chat("Compare dataset coverage"), "source_dataset_statistics")
    check_result_nonempty(tr)

# ===== CATEGORY D: CATALYST ANALYTICS =====

def test_d16_catalyst_stats():
    tr = assert_tool_result(post_chat("Show catalyst statistics"), "catalyst_statistics")
    check_result_nonempty(tr)

def test_d17_most_common():
    tr = assert_tool_result(post_chat("Most common catalysts"), "catalyst_statistics")
    check_result_nonempty(tr)

def test_d18_buchwald():
    tr = assert_tool_result(post_chat("Most common catalysts in Buchwald-Hartwig reactions"), "catalyst_statistics")
    check_result_nonempty(tr)

def test_d21_overall():
    tr = assert_tool_result(post_chat("Which catalysts appear most often overall?"), "catalyst_statistics")
    check_result_nonempty(tr)

def test_d22_palladium():
    tr = assert_tool_result(post_chat("Which catalysts contain palladium?"), "catalyst_statistics")
    check_result_nonempty(tr)

# ===== CATEGORY E: TEMPERATURE =====

def test_e26_temp_stats():
    tr = assert_tool_result(post_chat("Show temperature statistics"), "temperature_statistics")
    r = tr["result"]
    assert "clean_statistics" in r, "Expected clean_statistics in temperature result"
    cs = r["clean_statistics"]
    assert cs["count"] > 1_000_000, f"Expected >1M clean temp records, got {cs['count']}"

def test_e27_avg_temp():
    tr = assert_tool_result(post_chat("Average temperature"), "temperature_statistics")
    r = tr["result"]
    assert "clean_statistics" in r

def test_e28_median_temp():
    tr = assert_tool_result(post_chat("Median temperature"), "temperature_statistics")
    r = tr["result"]
    assert "clean_statistics" in r

# ===== CATEGORY F: YIELD =====

def test_f32_yield_stats():
    tr = assert_tool_result(post_chat("Show yield statistics"), "yield_statistics")
    r = tr["result"]
    assert "clean_statistics" in r, "Expected clean_statistics in yield result"
    cs = r["clean_statistics"]
    assert 50 < cs["average"] < 80, f"Expected clean avg yield 50-80%, got {cs['average']}"

def test_f33_avg_yield():
    tr = assert_tool_result(post_chat("Average yield"), "yield_statistics")
    r = tr["result"]
    assert "clean_statistics" in r

def test_f34_median_yield():
    tr = assert_tool_result(post_chat("Median yield"), "yield_statistics")
    r = tr["result"]
    assert "clean_statistics" in r

# ===== CATEGORY G: PROCEDURE SEARCH =====

def test_g38_palladium_procs():
    tr = assert_tool_result(post_chat("Show procedures mentioning palladium"), "search_procedures")
    assert tr["result"]["count"] > 0

def test_g40_chromatography():
    tr = assert_tool_result(post_chat("Show procedures mentioning chromatography"), "search_procedures")
    assert tr["result"]["count"] > 0

def test_g41_ethanol():
    tr = assert_tool_result(post_chat("Show procedures mentioning ethanol"), "search_procedures")
    assert tr["result"]["count"] > 0

def test_g42_reflux():
    tr = assert_tool_result(post_chat("Show procedures mentioning reflux"), "search_procedures")
    assert tr["result"]["count"] > 0

# ===== CATEGORY H: REACTION SEARCH =====

def test_h43_buchwald():
    tr = assert_tool_result(post_chat("Find Buchwald-Hartwig reactions"), "search_reactions")
    assert tr["result"]["count"] > 0

def test_h46_pd_catalyst():
    tr = assert_tool_result(post_chat("Find reactions containing palladium catalysts"))
    check_result_nonempty(tr)

def test_h47_cu_catalyst():
    tr = assert_tool_result(post_chat("Find reactions containing copper catalysts"))
    check_result_nonempty(tr)

def test_h48_boronic():
    tr = assert_tool_result(post_chat("Find reactions involving boronic acids"), "search_reactions")
    assert tr["result"]["count"] > 0

# ===== CATEGORY I: MOLECULE SEARCH =====

def test_i49_ethanol():
    tr = assert_tool_result(post_chat("Find ethanol"), "molecule_lookup")
    results = tr["result"].get("results", [])
    assert any("CCO" in str(r.get("smiles", "")) for r in results), "Ethanol (CCO) not found"

def test_i50_acetone():
    tr = assert_tool_result(post_chat("Find acetone"), "molecule_lookup")
    results = tr["result"].get("results", [])
    assert any("CC(C)=O" in str(r.get("smiles", "")) for r in results), "Acetone not found"

def test_i53_benzene():
    tr = assert_tool_result(post_chat("Find benzene-containing molecules"), "molecule_lookup")
    assert tr["result"]["count"] > 0

# ===== CATEGORY J: COMPARISON =====

def test_j54_compare_types():
    tr = assert_tool_result(post_chat("Compare Buchwald-Hartwig and Suzuki reactions"))
    check_result_nonempty(tr)

def test_j56_compare_datasets():
    tr = assert_tool_result(post_chat("Compare dataset coverage"), "source_dataset_statistics")
    check_result_nonempty(tr)

def test_j57_compare_temps():
    tr = assert_tool_result(post_chat("Compare temperature distributions"), "temperature_statistics")
    assert "clean_statistics" in tr["result"]

def test_j58_compare_yields():
    tr = assert_tool_result(post_chat("Compare yield distributions"), "yield_statistics")
    assert "clean_statistics" in tr["result"]

# ===== CATEGORY K: NATURAL LANGUAGE =====

def test_k59_bh_catalysts():
    tr = assert_tool_result(post_chat("What catalysts are commonly used for Buchwald-Hartwig chemistry?"), "catalyst_statistics")
    check_result_nonempty(tr)

def test_k61_richest_datasets():
    tr = assert_tool_result(post_chat("Which datasets are richest in experimental data?"), "source_dataset_statistics")
    check_result_nonempty(tr)

# ===== CATEGORY L: EDGE CASES =====

def test_l63_capital():
    assert_no_tool(post_chat("What is the capital of France?"))

def test_l64_joke():
    assert_no_tool(post_chat("Tell me a joke."))

def test_l65_quicksort():
    assert_no_tool(post_chat("Write a Python quicksort."))

def test_l66_quantum():
    assert_no_tool(post_chat("Explain quantum mechanics."))

def test_l67_gibberish():
    events = post_chat("asdfqwer zxcvjklm")
    # Either no_tool or tool_result; must NOT be a system error
    assert not any(e.get("type") == "error" for e in events if "Network error" in str(e.get("message", ""))), \
        "Unexpected network error for gibberish input"

def test_l68_long_prompt():
    events = post_chat("What reaction types have data? " * 50)
    assert has_type(events, "done"), "Long prompt should complete"

# ===== CATEGORY N: REAGENT STATISTICS (new tool) =====

def test_n_reagent_stats():
    tr = assert_tool_result(post_chat("What solvents are most commonly used?"))
    check_result_nonempty(tr)


if __name__ == "__main__":
    print("=" * 60)
    print("ORD AI Chemistry Engine - Capability Audit Tests")
    print("=" * 60)

    print("\nCATEGORY A — Database Summary")
    run("A1: Summarize database", test_a1_summarize)
    run("A2: Reaction count", test_a2_reaction_count)
    run("A3: Procedure count", test_a3_procedure_count)
    run("A4: Molecule count", test_a4_molecule_count)
    run("A5: Dataset count", test_a5_dataset_count)

    print("\nCATEGORY B — Reaction Types")
    run("B6: Types available", test_b6_reaction_types)
    run("B7: Most common type", test_b7_most_common_type)
    run("B8: Most procedures", test_b8_most_procedures)
    run("B9: Most yield info", test_b9_most_yield)
    run("B10: Most temp info", test_b10_most_temp)

    print("\nCATEGORY C — Source Datasets")
    run("C11: Most reactions", test_c11_most_reactions)
    run("C12: Most procedures", test_c12_most_procedures)
    run("C13: Most yield", test_c13_most_yield)
    run("C14: Most temp", test_c14_most_temp)
    run("C15: Compare coverage", test_c15_compare)

    print("\nCATEGORY D — Catalyst Analytics")
    run("D16: Catalyst stats", test_d16_catalyst_stats)
    run("D17: Most common", test_d17_most_common)
    run("D18: Buchwald-Hartwig", test_d18_buchwald)
    run("D21: Overall catalysts", test_d21_overall)
    run("D22: Palladium catalysts", test_d22_palladium)

    print("\nCATEGORY E — Temperature Analytics")
    run("E26: Temp stats + clean_statistics", test_e26_temp_stats)
    run("E27: Avg temperature", test_e27_avg_temp)
    run("E28: Median temperature", test_e28_median_temp)

    print("\nCATEGORY F — Yield Analytics")
    run("F32: Yield stats + clean_statistics", test_f32_yield_stats)
    run("F33: Avg yield", test_f33_avg_yield)
    run("F34: Median yield", test_f34_median_yield)

    print("\nCATEGORY G — Procedure Search")
    run("G38: Palladium procs", test_g38_palladium_procs)
    run("G40: Chromatography", test_g40_chromatography)
    run("G41: Ethanol", test_g41_ethanol)
    run("G42: Reflux", test_g42_reflux)

    print("\nCATEGORY H — Reaction Search")
    run("H43: Buchwald-Hartwig", test_h43_buchwald)
    run("H46: Palladium catalyst", test_h46_pd_catalyst)
    run("H47: Copper catalyst", test_h47_cu_catalyst)
    run("H48: Boronic acid", test_h48_boronic)

    print("\nCATEGORY I — Molecule Search")
    run("I49: Ethanol", test_i49_ethanol)
    run("I50: Acetone", test_i50_acetone)
    run("I53: Benzene", test_i53_benzene)

    print("\nCATEGORY J — Comparison Queries")
    run("J54: Compare reaction types", test_j54_compare_types)
    run("J56: Compare datasets", test_j56_compare_datasets)
    run("J57: Compare temps", test_j57_compare_temps)
    run("J58: Compare yields", test_j58_compare_yields)

    print("\nCATEGORY K — Natural Language")
    run("K59: BH catalysts", test_k59_bh_catalysts)
    run("K61: Richest datasets", test_k61_richest_datasets)

    print("\nCATEGORY L — Edge Cases")
    run("L63: Capital of France", test_l63_capital)
    run("L64: Tell me a joke", test_l64_joke)
    run("L65: Python quicksort", test_l65_quicksort)
    run("L66: Quantum mechanics", test_l66_quantum)
    run("L67: Gibberish", test_l67_gibberish)
    run("L68: Long prompt", test_l68_long_prompt)

    print("\nCATEGORY N — Reagent Statistics (new tool)")
    run("N: Common solvents", test_n_reagent_stats)

    print()
    print("=" * 60)
    total = PASS + FAIL
    print(f"RESULTS: {PASS}/{total} PASSED ({100*PASS//total}%)")
    if FAIL:
        print("FAILED tests require investigation.")
    else:
        print("All tests passed.")
    print("=" * 60)
    sys.exit(0 if FAIL == 0 else 1)
