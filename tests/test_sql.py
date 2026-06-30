import duckdb
import json
import traceback

con = duckdb.connect("backend/database/ord.duckdb", read_only=True)

def test_compare_datasets():
    print("\n--- TEST: compare_datasets ---")
    query = """
    SELECT 
        source_dataset, 
        COUNT(DISTINCT r.reaction_id) as reaction_count,
        COUNT(p.reaction_id) as procedure_count,
        AVG(p.yield_percent) as avg_yield
    FROM reactions r
    LEFT JOIN procedures p ON r.reaction_id = p.reaction_id
    GROUP BY source_dataset
    ORDER BY reaction_count DESC
    LIMIT 2;
    """
    try:
        df = con.execute(query).df()
        print(df.to_string())
    except Exception as e:
        print("Failed:", e)

def test_top_yield_conditions():
    print("\n--- TEST: top_yield_conditions ---")
    query = """
    SELECT 
        r.reaction_type,
        c.catalyst as catalyst,
        COUNT(*) as freq,
        AVG(p.yield_percent) as avg_yield
    FROM reactions r
    JOIN procedures p ON r.reaction_id = p.reaction_id
    JOIN (
      SELECT reaction_id, unnest(from_json(catalysts_json, '["VARCHAR"]')) as catalyst 
      FROM reactions
      WHERE catalysts_json IS NOT NULL
    ) c ON c.reaction_id = r.reaction_id
    WHERE r.reaction_type IS NOT NULL
    AND p.yield_percent IS NOT NULL
    GROUP BY r.reaction_type, c.catalyst
    HAVING COUNT(*) > 10
    ORDER BY avg_yield DESC
    LIMIT 5;
    """
    try:
        df = con.execute(query).df()
        print(df.to_string())
    except Exception as e:
        print("Failed:")
        traceback.print_exc()

def test_dataset_quality_report():
    print("\n--- TEST: dataset_quality_report ---")
    query = """
    SELECT
        COUNT(r.reaction_id) as total_reactions,
        SUM(CASE WHEN r.reaction_type IS NOT NULL THEN 1 ELSE 0 END) as reactions_with_type,
        COUNT(p.reaction_id) as total_procedures,
        SUM(CASE WHEN p.yield_percent IS NOT NULL THEN 1 ELSE 0 END) as procedures_with_yield,
        SUM(CASE WHEN p.temperature_c IS NOT NULL THEN 1 ELSE 0 END) as procedures_with_temp
    FROM reactions r
    LEFT JOIN procedures p ON r.reaction_id = p.reaction_id;
    """
    try:
        df = con.execute(query).df()
        print(df.to_string())
    except Exception as e:
        print("Failed:", e)

test_compare_datasets()
test_top_yield_conditions()
test_dataset_quality_report()
