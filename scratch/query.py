import duckdb
import json
con = duckdb.connect('backend/database/ord.duckdb', read_only=True)
print("Aniline count:")
print(con.execute("SELECT COUNT(*) FROM reactions WHERE CAST(reactants_json AS VARCHAR) ILIKE '%Aniline%'").fetchone())
print("Diphenylamine count:")
print(con.execute("SELECT COUNT(*) FROM reactions WHERE CAST(products_json AS VARCHAR) ILIKE '%Diphenylamine%'").fetchone())
print("Both count:")
print(con.execute("SELECT COUNT(*) FROM reactions WHERE CAST(reactants_json AS VARCHAR) ILIKE '%Aniline%' AND CAST(products_json AS VARCHAR) ILIKE '%Diphenylamine%'").fetchone())
