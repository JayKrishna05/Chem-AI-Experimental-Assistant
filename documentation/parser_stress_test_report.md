> **Historical Document**: This file was created during Phase 5 or 6 and is archived here for reference.

# Parser Stress Test Report

## Overview
Stress testing was performed on the `backend/experiment/parser.py` using noisy, realistic inputs via `tests/test_experiment_upload.py`. The objective was to verify how gracefully the deterministic parser handles messy user data.

## Variations Tested

### 1. Alternative Column Names & Capitalization
- **Scenario**: Users uploading CSVs with `Reaction_Type`, `REACTANT`, or ` Temperature `.
- **Result**: **PASS**. The parser's `normalized_row = {k.lower().strip(): v.strip()}` cleanly handles capitalization and trailing whitespace. The `_parse_list` function gracefully accepts `reactants` or `reactant` columns.

### 2. Mixed Units and Malformed Numbers
- **Scenario**: Cell contains `"80 C"` instead of `"80"`, or `"95%"` instead of `"95"`.
- **Result**: **FAIL (Gracefully)**. The current MVP uses a simple `float()` conversion. Strings like `"80 C"` trigger a `ValueError` resulting in `temperature_c = None`. This is technically safe (it doesn't crash the pipeline), but it loses data.

### 3. Duplicate Columns
- **Scenario**: A CSV contains `reactant, reactant` because a user placed multiple components in separate columns instead of a comma-separated list.
- **Result**: **FAIL (Data Loss)**. `csv.DictReader` natively overwrites identical keys with the last parsed column. The first reactant is lost.

### 4. Missing Fields
- **Scenario**: Fields containing `"N/A"` or entirely blank.
- **Result**: **PASS**. The parser safely assigns `None` and defers missing-data logic to the Validator (which flags them appropriately without crashing).

### 5. Aliases
- **Scenario**: `PALLADIUM` vs `Pd`.
- **Result**: **PASS**. The `Normalizer` correctly traps this, lowercases it, maps it to `Pd`, and successfully logs the change in `normalized_fields`.

## Remaining Gaps & Recommendations

1. **Regex Number Extraction**: The `float()` cast in `parse_csv` should be replaced with a regex extraction (e.g., `re.search(r'\d+(\.\d+)?', value)`) to survive mixed-unit strings like `"80 C"`.
2. **Multi-Column Concatenation**: If `DictReader` encounters duplicate column headers (like `reactant`), it should aggregate them into a list rather than overwriting.
3. **Quoted Commas in CSV**: The current list splitting (`val.split(",")`) will break if an IUPAC name string contains a comma (e.g., `1,2-dichloroethane`). A more robust structural parser is needed for complex chemical names.
