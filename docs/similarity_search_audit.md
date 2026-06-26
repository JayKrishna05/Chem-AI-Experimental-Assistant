# Similarity Search Audit

This report investigates why the "Similar Reactions" metric in the upload pipeline returns 0 matches for certain valid experiments (specifically, the Buchwald-Hartwig amination test fixture).

## 1. Uploaded CanonicalExperiment
The test upload provided the following structure:
```json
{
  "reaction_type": "Buchwald-Hartwig amination",
  "reactants": ["Aniline", "Bromobenzene"],
  "reagents": ["Sodium tert-butoxide"],
  "catalysts": ["Pd2(dba)3"],
  "products": ["Diphenylamine"],
  "temperature_c": 100,
  "yield_percent": 82
}
```

## 2. Normalization Process
The `normalizer.py` applied the following transformations:
- **`reaction_type`**: Title-cased to "Buchwald-Hartwig Amination".
- **Whitespace**: Stripped from all list elements.
- **Catalysts**: Did not match any known element aliases (like "palladium" -> "Pd"), so remained `["Pd2(dba)3"]`.

## 3. Matching Strategy (`comparison_service.py`)
To prevent excessively restrictive queries, the comparison service employs a heuristic: it only checks the **first** reactant and the **first** product.
```python
res = search_reactions(
    reactant=exp.reactants[0], # "Aniline"
    product=exp.products[0],   # "Diphenylamine"
    limit=5
)
```

## 4. SQL Filters (`filters.py`)
The `search_reactions` tool delegates to `build_filters`, which generates a `WHERE` clause using `ILIKE` on casted JSON text:
```sql
WHERE CAST(r.reactants_json AS VARCHAR) ILIKE '%Aniline%' 
  AND CAST(r.products_json AS VARCHAR) ILIKE '%Diphenylamine%'
```

## 5. Database Contents & Root Cause
A manual audit of the DuckDB snapshot (`ord.duckdb`) revealed:
- `SELECT COUNT(*) FROM reactions WHERE CAST(reactants_json AS VARCHAR) ILIKE '%Aniline%'` -> **960 rows**
- `SELECT COUNT(*) FROM reactions WHERE CAST(products_json AS VARCHAR) ILIKE '%Diphenylamine%'` -> **0 rows**

**Conclusion:** The query successfully executed, but it returned 0 matches because the specific string "Diphenylamine" does not exist anywhere within the `products_json` column in this database snapshot. 

This indicates that either:
1. The dataset strictly uses alternative nomenclature (e.g., IUPAC names or SMILES strings) for this specific product.
2. The snapshot simply does not contain this specific Buchwald-Hartwig reaction.

*Note: The "Optimal Conditions Comparison" relies solely on `reaction_type`, which successfully matched over 1,200 rows, explaining why the analytics succeeded overall while the similarity search yielded 0.*
