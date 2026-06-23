import duckdb
import pandas as pd
from collections import defaultdict

con = duckdb.connect("backend/database/ord.duckdb")

def audit_catalysts():
    print("Extracting unique catalyst entries from database...")
    query = """
    SELECT 
        COALESCE(json_extract_string(c.value, '$.smiles'), '') AS smiles,
        COALESCE(json_extract_string(c.value, '$.name'), '') AS name,
        COUNT(*) as freq
    FROM reactions r, json_each(r.catalysts_json) c
    WHERE r.catalysts_json IS NOT NULL
    GROUP BY smiles, name
    HAVING smiles != '' OR name != ''
    ORDER BY freq DESC
    """
    
    df = con.execute(query).df()
    
    total_distinct = len(df)
    print(f"Total distinct (smiles, name) pairs: {total_distinct}")
    
    smiles_to_names = defaultdict(list)
    name_to_smiles = defaultdict(list)
    
    for _, row in df.iterrows():
        s = row['smiles']
        n = row['name']
        f = row['freq']
        
        if s:
            smiles_to_names[s].append((n, f))
        if n:
            name_to_smiles[n].append((s, f))
            
    smiles_with_multiple_names = {s: names for s, names in smiles_to_names.items() if len(set([n[0] for n in names if n[0]])) > 1}
    names_with_multiple_smiles = {n: smiles for n, smiles in name_to_smiles.items() if len(set([s[0] for s in smiles if s[0]])) > 1}
    
    with open("catalyst_normalization_report.md", "w") as f:
        f.write("# Catalyst Identifier Normalization Report\\n\\n")
        f.write(f"**Total distinct (SMILES, Name) pairs extracted:** {total_distinct}\\n")
        f.write(f"**Unique SMILES strings:** {len(smiles_to_names)}\\n")
        f.write(f"**Unique Names:** {len(name_to_smiles)}\\n\\n")
        
        f.write("## 1. Identical SMILES with Multiple Names\\n")
        f.write("This indicates that the same chemical structure is referred to by different names. If we group by name alone, these will be falsely separated.\\n\\n")
        count = 0
        for s, names in sorted(smiles_with_multiple_names.items(), key=lambda x: -sum(n[1] for n in x[1])):
            if count >= 15: break
            f.write(f"- **SMILES:** `{s}`\\n")
            for n, freq in names:
                name_str = f'"{n}"' if n else "(empty name)"
                f.write(f"  - {name_str} (freq: {freq})\\n")
            count += 1
            
        f.write("\\n## 2. Identical Names with Multiple SMILES\\n")
        f.write("This indicates that the same name resolves to different structures (or missing structures). If we group by name, we might wrongly merge distinct species or varying purities.\\n\\n")
        count = 0
        for n, smiles in sorted(names_with_multiple_smiles.items(), key=lambda x: -sum(s[1] for s in x[1])):
            if count >= 15: break
            f.write(f"- **Name:** `\"{n}\"`\\n")
            for s, freq in smiles:
                smiles_str = f"`{s}`" if s else "(empty SMILES)"
                f.write(f"  - {smiles_str} (freq: {freq})\\n")
            count += 1
            
        f.write("\\n## 3. Empty SMILES vs Name\\n")
        empty_smiles_count = sum(freq for names in name_to_smiles.values() for s, freq in names if not s)
        empty_name_count = sum(freq for smiles in smiles_to_names.values() for n, freq in smiles if not n)
        f.write(f"- Mentions missing SMILES entirely: {empty_smiles_count}\\n")
        f.write(f"- Mentions missing Names entirely: {empty_name_count}\\n\\n")
        
        f.write("## 4. Conclusion on `compare_catalysts` tool\\n")
        f.write("Without a normalization lookup table, comparing catalysts by string-matching their `name` or `smiles` directly from the JSON array will be **misleading**.\\n")
        f.write("A catalyst like 'Pd/C' might appear under several name variants or missing SMILES strings. ")
        f.write("We recommend building a `catalyst_normalization` table in DuckDB to collapse synonyms to a canonical identifier before implementing a public-facing comparison tool.\\n")

    print("Report written to catalyst_normalization_report.md")

audit_catalysts()
