import duckdb

con = duckdb.connect('backend/database/ord.duckdb', read_only=True)

# Source datasets
print('=== SOURCE DATASETS (top 10 by reaction count) ===')
rows = con.execute('SELECT source_dataset, COUNT(*) AS cnt FROM reactions GROUP BY source_dataset ORDER BY cnt DESC LIMIT 10').fetchall()
for r in rows:
    print(f'  {r[0]!r}: {r[1]:,}')

# Catalyst search example - palladium
print()
print('=== CATALYST SEARCH SAMPLE (palladium) ===')
rows = con.execute("""
SELECT COALESCE(json_extract_string(c.value, '$.smiles'), '') AS cs,
       COALESCE(json_extract_string(c.value, '$.name'), '') AS cn,
       COUNT(*) AS cnt
FROM reactions AS r, json_each(r.catalysts_json) AS c
WHERE COALESCE(json_extract_string(c.value, '$.smiles'), '') ILIKE '%Pd%'
   OR COALESCE(json_extract_string(c.value, '$.name'), '') ILIKE '%palladium%'
GROUP BY cs, cn ORDER BY cnt DESC LIMIT 5
""").fetchall()
for r in rows:
    print(f'  smiles={r[0]!r} name={r[1]!r} cnt={r[2]}')

# Yield stats global
print()
print('=== YIELD STATISTICS (global) ===')
row = con.execute('SELECT COUNT(*) as n, AVG(yield_percent) as avg, MEDIAN(yield_percent) as med, MIN(yield_percent) as mn, MAX(yield_percent) as mx FROM procedures WHERE yield_percent IS NOT NULL AND isfinite(yield_percent)').fetchone()
print(f'n={row[0]:,} avg={row[1]:.2f} med={row[2]:.2f} min={row[3]:.2f} max={row[4]:.2f}')

# Temperature stats global
print()
print('=== TEMPERATURE STATISTICS (global) ===')
row = con.execute('SELECT COUNT(*) as n, AVG(temperature_c) as avg, MEDIAN(temperature_c) as med, MIN(temperature_c) as mn, MAX(temperature_c) as mx FROM procedures WHERE temperature_c IS NOT NULL AND isfinite(temperature_c)').fetchone()
print(f'n={row[0]:,} avg={row[1]:.2f} med={row[2]:.2f} min={row[3]:.2f} max={row[4]:.2f}')

# Molecule lookup
print()
print('=== MOLECULE LOOKUP (top 5 by occurrences) ===')
rows = con.execute('SELECT smiles, occurrences FROM molecules ORDER BY occurrences DESC LIMIT 5').fetchall()
for r in rows:
    print(f'  {r[0]!r}: {r[1]:,}')

# Procedures text sample
print()
print('=== PROCEDURE TEXT SAMPLE (palladium) ===')
rows = con.execute("SELECT procedure_text FROM procedures WHERE procedure_text ILIKE '%palladium%' LIMIT 2").fetchall()
for r in rows:
    print(f'  {r[0][:120]!r}')

# Reaction search - boronic acid
print()
print('=== SEARCH REACTIONS (boronic acid in reactants) ===')
row = con.execute("SELECT COUNT(*) FROM reactions WHERE CAST(reactants_json AS VARCHAR) ILIKE '%boronic%'").fetchone()
print(f'  Reactions with boronic in reactants: {row[0]:,}')

# Molecule named search (caffeine, aspirin, ethanol, acetone, benzene)
print()
print('=== MOLECULE LOOKUP (named) ===')
for name in ['CCO', 'CC(C)=O', 'c1ccccc1', 'Cn1cnc2c1c(=O)n(c(=O)n2C)C', 'CC(=O)Oc1ccccc1C(=O)O']:
    row = con.execute(f"SELECT occurrences FROM molecules WHERE smiles = '{name}'").fetchone()
    print(f'  {name!r}: {row[0] if row else 0:,}')

# Check procedure_text search for chromatography, reflux, ethanol, copper
for kw in ['chromatography', 'reflux', 'ethanol', 'copper']:
    row = con.execute(f"SELECT COUNT(*) FROM procedures WHERE procedure_text ILIKE '%{kw}%'").fetchone()
    print(f'  procedures with {kw!r}: {row[0]:,}')
