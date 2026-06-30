> **Historical Document**: This file was created during Phase 5 or 6 and is archived here for reference.

# Tool Coverage Audit & Gap Report

## Current Coverage Analysis
Based on our expanded 100-case benchmark dataset across 10 chemistry analytical categories, the current tool coverage is:
- **Supported (50/100):** Can be answered perfectly with existing tools.
- **Partially Supported (10/100):** Tool exists but lacks specific filters or depth (e.g., molecule name lookup relying entirely on LLM SMILES generation, or missing temporal trends).
- **Unsupported (40/100):** Cannot be answered with the current toolset.

**Current Coverage Score:** `55.0%`

## Detailed Gap Report

### 1. Comparative Chemistry
- **Missing Capability:** No tools exist to compare multiple entities (catalysts, datasets, reaction conditions) side-by-side.
- **Priority:** High
- **Suggested Tools:** `compare_catalysts`, `compare_datasets`

### 2. Experimental Design
- **Missing Capability:** No way to recommend conditions, solvents, or catalysts based on yield optimization.
- **Priority:** High
- **Suggested Tools:** `top_yield_conditions`, `catalyst_yield_correlation`

### 3. Database Exploration (Quality & Depth)
- **Missing Capability:** Users want to evaluate data quality before trusting it, but we only have record counts.
- **Priority:** Medium
- **Suggested Tools:** `dataset_quality_report`

### 4. Similarity Search
- **Missing Capability:** Structural similarity for molecules, analogous reactions, and semantic search over procedures.
- **Priority:** Low (Requires Phase 5/6 Infrastructure - pgvector, RDKit, Embeddings)

### 5. File Upload Workflows
- **Missing Capability:** Analyzing user-uploaded SDF, CSV, or PDF papers.
- **Priority:** Low (Requires Phase 5 Infrastructure)

---

## High-Value Tool Proposals (Phase 4 DuckDB Implementation)

We will immediately implement the following tools, as they rely entirely on the existing DuckDB dataset and require no external infrastructure.

### 1. `compare_datasets`
- **Purpose:** Compare two source datasets side-by-side across reaction counts, procedure counts, and average yields.
- **Input Schema:** `{"dataset_a": str, "dataset_b": str}`
- **DuckDB Strategy:** Two parallel aggregate queries grouped by dataset ID.

### 2. `compare_catalysts`
- **Purpose:** Compare the frequency and average yield of two different catalysts within a specific reaction class.
- **Input Schema:** `{"catalyst_a": str, "catalyst_b": str, "reaction_type": Optional[str]}`
- **DuckDB Strategy:** Aggregate `reaction_count` and `AVG(yield)` WHERE catalyst IN (A, B), grouped by catalyst.

### 3. `top_yield_conditions`
- **Purpose:** Find the optimal reaction conditions (temperature, solvent, catalyst) that produce the highest average yields for a given reaction type.
- **Input Schema:** `{"reaction_type": str, "limit": int}`
- **DuckDB Strategy:** Group by catalyst/solvent, calculate median/avg yield, order by yield DESC.

### 4. `catalyst_yield_correlation`
- **Purpose:** Analyze how different catalysts impact the yield distribution of a specific reaction.
- **Input Schema:** `{"reaction_type": str, "limit": int}`
- **DuckDB Strategy:** Group by catalyst, calculate AVG(yield) and count, order by count DESC.

### 5. `dataset_quality_report`
- **Purpose:** Report on the completeness of data (percentage of non-null yields, non-null temperatures, specified catalysts) across the database or a specific reaction type.
- **Input Schema:** `{"reaction_type": Optional[str]}`
- **DuckDB Strategy:** `COUNT(yield) / COUNT(*)` ratios across the procedures table.

---

## Coverage Roadmap

| Phase | Description | Projected Coverage % |
|-------|-------------|----------------------|
| **Current** | Baseline set of 10 tools. | 55.0% |
| **Phase 4 (Target)** | Adding comparative tools, experimental design (DuckDB-only). | ~70.0% |
| **Phase 5** | Similarity search (pgvector), embeddings, user file uploads. | ~85.0% |
| **Phase 6** | Predictive models, RDKit sub-structure search. | > 95.0% |
