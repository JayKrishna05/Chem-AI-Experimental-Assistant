import duckdb

con = duckdb.connect('backend/database/ord.duckdb', read_only=True)

# Yield data quality - examine range of yield values to find if there are outliers making the avg nonsensical
print('=== YIELD DISTRIBUTION ANALYSIS ===')
rows = con.execute("""
SELECT
  CASE
    WHEN yield_percent < 0 THEN 'negative'
    WHEN yield_percent BETWEEN 0 AND 100 THEN 'valid (0-100%)'
    WHEN yield_percent BETWEEN 100 AND 1000 THEN 'slightly high (100-1000%)'
    ELSE 'extreme outlier (>1000%)'
  END AS bucket,
  COUNT(*) AS cnt
FROM procedures
WHERE yield_percent IS NOT NULL AND isfinite(yield_percent)
GROUP BY bucket ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f'  {r[0]}: {r[1]:,}')

print()
print('=== EXTREME YIELD OUTLIERS (top 10) ===')
rows = con.execute('SELECT yield_percent, reaction_type FROM procedures WHERE yield_percent IS NOT NULL AND isfinite(yield_percent) ORDER BY yield_percent DESC LIMIT 10').fetchall()
for r in rows:
    print(f'  {r[0]} ({r[1]!r})')

print()
print('=== YIELD STATS (valid range 0-100 only) ===')
row = con.execute('SELECT COUNT(*) as n, AVG(yield_percent) as avg, MEDIAN(yield_percent) as med FROM procedures WHERE yield_percent >= 0 AND yield_percent <= 100').fetchone()
print(f'n={row[0]:,} avg={row[1]:.2f} med={row[2]:.2f}')

# Temperature quality
print()
print('=== TEMPERATURE DISTRIBUTION ===')
rows = con.execute("""
SELECT
  CASE
    WHEN temperature_c < -100 THEN 'very cold (< -100°C)'
    WHEN temperature_c BETWEEN -100 AND 0 THEN 'cold (-100 to 0°C)'
    WHEN temperature_c BETWEEN 0 AND 200 THEN 'normal (0-200°C)'
    WHEN temperature_c BETWEEN 200 AND 1000 THEN 'high (200-1000°C)'
    ELSE 'extreme (>1000°C)'
  END AS bucket,
  COUNT(*) AS cnt
FROM procedures
WHERE temperature_c IS NOT NULL AND isfinite(temperature_c)
GROUP BY bucket ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f'  {r[0]}: {r[1]:,}')

print()
print('=== TEMP STATS (valid range -100 to 300°C) ===')
row = con.execute('SELECT COUNT(*) as n, AVG(temperature_c) as avg, MEDIAN(temperature_c) as med FROM procedures WHERE temperature_c >= -100 AND temperature_c <= 300').fetchone()
print(f'n={row[0]:,} avg={row[1]:.2f} med={row[2]:.2f}')

# Check what Suzuki / amide coupling reactions look like
print()
print('=== REACTION TYPE PATTERN SEARCH ===')
for kw in ['Suzuki', 'amide', 'Heck', 'boronic', 'coupling']:
    row = con.execute(f"SELECT COUNT(*) FROM reactions WHERE reaction_type ILIKE '%{kw}%'").fetchone()
    print(f'  reactions with {kw!r} in type: {row[0]:,}')

# Test search_reactions for catalysts containing palladium  
print()
print('=== REACTIONS with catalyst containing Pd ===')
row = con.execute("SELECT COUNT(*) FROM reactions WHERE CAST(catalysts_json AS VARCHAR) ILIKE '%Pd%'").fetchone()
print(f'  {row[0]:,}')

print()
print('=== REACTIONS with catalyst containing Cu ===')
row = con.execute("SELECT COUNT(*) FROM reactions WHERE CAST(catalysts_json AS VARCHAR) ILIKE '%Cu%'").fetchone()
print(f'  {row[0]:,}')

# Check if reaction_type is almost always None
print()
print('=== REACTION_TYPE NULL RATIO ===')
row = con.execute("SELECT COUNT(*) FROM reactions WHERE reaction_type IS NULL").fetchone()
print(f'  NULL reaction_type: {row[0]:,}')
row = con.execute("SELECT COUNT(*) FROM reactions WHERE reaction_type IS NOT NULL").fetchone()
print(f'  Non-NULL reaction_type: {row[0]:,}')
