from backend.tools.analytics_tools import compare_datasets, top_yield_conditions, dataset_quality_report
import os

DB_PATH = os.path.join("backend", "database", "ord.duckdb")

def test_compare_datasets():
    print("Testing compare_datasets...")
    res = compare_datasets(group_by="source_dataset", database_path=DB_PATH)
    assert res["tool"] == "compare_datasets"
    assert "results" in res
    assert len(res["results"]) > 0
    
    # Check shape of result
    first = res["results"][0]
    assert "dataset_name" in first
    assert "reaction_count" in first
    assert "avg_yield" in first

def test_top_yield_conditions():
    print("Testing top_yield_conditions...")
    res = top_yield_conditions(database_path=DB_PATH)
    assert res["tool"] == "top_yield_conditions"
    assert "results" in res
    assert len(res["results"]) > 0
    
    # Check shape of result
    first = res["results"][0]
    assert "reaction_type" in first
    assert "catalyst" in first
    assert "avg_yield" in first

def test_dataset_quality_report():
    print("Testing dataset_quality_report...")
    res = dataset_quality_report(database_path=DB_PATH)
    assert res["tool"] == "dataset_quality_report"
    assert "results" in res
    assert "total_reactions" in res["results"]
    assert "procedures_with_yield" in res["results"]

if __name__ == "__main__":
    test_compare_datasets()
    test_top_yield_conditions()
    test_dataset_quality_report()
    print("All tests passed.")
