# Filter Consistency Audit

This document reviews the supported, dropped, and silently ignored filters across all search, analytics, and comparison-related DuckDB tools in the ORD Chemistry Engine.

## Search Tools

### `search_reactions`
* **Supported Filters**: `reaction_id`, `reaction_type`, `source_dataset`, `source_dataset_id`, `reactant`, `reagent`, `catalyst`, `product`
* **Consistency Issues**: 
  * JSON arrays (`reactants_json`, etc.) are cast to `VARCHAR` and queried via `ILIKE`. Searching for a catalyst like "Pd" will match any string containing "Pd" (e.g. "Pd(OAc)2" or even unrelated words).
* **Priority**: Medium
* **Risk**: Returning false positives for short text queries, but generally safe since users can read the results.

### `search_procedures`
* **Supported Filters**: `reaction_id`, `reaction_type`, `text`, `temperature_min`, `temperature_max`, `yield_min`, `yield_max`
* **Consistency Issues**: None. All filters are safely parameterized.
* **Priority**: Low

### `molecule_lookup`
* **Supported Filters**: `smiles`, `query`, `min_occurrences`
* **Consistency Issues**: None.
* **Priority**: Low

## Analytics Tools

### `compare_datasets`
* **Supported Filters**: `group_by`
* **Silently Dropped Filters**: Any chemistry filter (e.g., `reaction_type`, `source_dataset`, `catalyst`).
* **Consistency Issues**: This tool accepts **no** filtering criteria whatsoever. If a user asks "Compare yields between USPTO and CJC for Suzuki coupling", the tool will silently drop the "Suzuki coupling" filter and compare the yields across the *entire* datasets.
* **Priority**: **Critical**
* **Risk**: The user receives a statistical answer to a completely different (global) question without any warning that their chemical filter was ignored.

### `top_yield_conditions`
* **Supported Filters**: `reaction_type`
* **Silently Dropped Filters**: `source_dataset`
* **Consistency Issues**: It ignores `source_dataset`. If the user asks for "top yield conditions for Buchwald in the USPTO dataset", it drops the dataset filter and searches the entire database. Furthermore, this tool isn't even exposed in the FastAPI routes (`routes.py`).
* **Priority**: **Critical**
* **Risk**: High risk of answering a different question than asked by silently ignoring the dataset constraint.

### `catalyst_statistics`, `reagent_statistics`
* **Supported Filters**: `reaction_type`, `source_dataset`
* **Consistency Issues**: None. Filters apply consistently.
* **Priority**: Low

### `yield_statistics`, `temperature_statistics`
* **Supported Filters**: `reaction_type`, `source_dataset`
* **Consistency Issues**: None. Filters apply consistently via `_reaction_filters`.
* **Priority**: Low

### `source_dataset_statistics`
* **Supported Filters**: `reaction_type`
* **Consistency Issues**: None.
* **Priority**: Low

### `reaction_type_statistics`
* **Supported Filters**: `source_dataset`
* **Consistency Issues**: None.
* **Priority**: Low

### `dataset_summary`, `dataset_quality_report`
* **Supported Filters**: None (Global statistics)
* **Consistency Issues**: None.
* **Priority**: Low
