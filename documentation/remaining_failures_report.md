> **Historical Document**: This file was created during Phase 5 or 6 and is archived here for reference.

# Remaining Failures Analysis

**Total Remaining Failures:** 42 (representing the 42% accuracy gap)

## 1. Summary Table

| Failure Cause | Count | Difficulty | Expected Gain |
| ------------- | ----- | ---------- | ------------- |
| Unsupported Workflow / Missing Tool | 25 | High (Requires Phase 5) | 25% |
| Filter Selection Error | 11 | Medium (Prompt/Schema Tuning) | 11% |
| Planner Routing Error | 6 | Low (Few-shot Examples) | 6% |

## 2. Detailed Breakdown

### Unsupported Workflow / Missing Tool
- **Failure count:** 25
- **Percentage:** 59.5%
- **Estimated Implementation Effort:** High (Requires Phase 5)
- **Estimated Benchmark Gain:** 25%

**Representative Examples:**
- **Query:** `Search molecules similar to aspirin`
  - Expected: `__none__` (Filters: `{}`)
  - Actual: `molecule_lookup` (Filters: `{'query': 'aspirin'}`)
- **Query:** `Compare palladium and copper catalysts`
  - Expected: `__none__` (Filters: `{}`)
  - Actual: `catalyst_statistics` (Filters: `{'limit': 50}`)
- **Query:** `Which catalyst gives the highest yield?`
  - Expected: `__none__` (Filters: `{}`)
  - Actual: `top_yield_conditions` (Filters: `{'reaction_type': 'Buchwald-Hartwig'}`)

### Filter Selection Error
- **Failure count:** 11
- **Percentage:** 26.2%
- **Estimated Implementation Effort:** Medium (Prompt/Schema Tuning)
- **Estimated Benchmark Gain:** 11%

**Representative Examples:**
- **Query:** `Which datasets have the most reactions?`
  - Expected: `source_dataset_statistics` (Filters: `{'sort_by': 'reaction_count'}`)
  - Actual: `source_dataset_statistics` (Filters: `{}`)
- **Query:** `Compare source datasets`
  - Expected: `compare_datasets` (Filters: `{'group_by': 'source_dataset'}`)
  - Actual: `compare_datasets` (Filters: `{}`)
- **Query:** `Which datasets contain the most procedures?`
  - Expected: `source_dataset_statistics` (Filters: `{'sort_by': 'procedure_count'}`)
  - Actual: `source_dataset_statistics` (Filters: `{}`)

### Planner Routing Error
- **Failure count:** 6
- **Percentage:** 14.3%
- **Estimated Implementation Effort:** Low (Few-shot Examples)
- **Estimated Benchmark Gain:** 6%

**Representative Examples:**
- **Query:** `Search for acetone`
  - Expected: `molecule_lookup` (Filters: `{'smiles': 'CC(C)=O'}`)
  - Actual: `search_reactions` (Filters: `{'reactant': 'acetone'}`)
- **Query:** `Molecule information for caffeine`
  - Expected: `search_procedures` (Filters: `{'text': 'caffeine'}`)
  - Actual: `molecule_lookup` (Filters: `{'query': 'caffeine'}`)
- **Query:** `Molecule details for water`
  - Expected: `search_procedures` (Filters: `{'text': 'water'}`)
  - Actual: `molecule_lookup` (Filters: `{'smiles': 'H2O'}`)

