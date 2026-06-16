# ORD Experimental Intelligence Assistant

## Overview

ORD Experimental Intelligence Assistant is a local-first AI system designed to help chemists explore, analyze, and compare reaction knowledge contained within the Open Reaction Database (ORD).

The system combines:

- Structured ORD reaction data
- Experimental procedures
- Molecule registry data
- Local and cloud LLMs
- Retrieval and analytics tools

into a single chat-based interface.

The goal is to create an AI-powered experimental intelligence platform capable of helping researchers discover relevant reactions, analyze experimental conditions, and compare new experiments against historical data.

---

# Core Objectives

The system should enable users to:

### Search Reactions

- Find reactions by reaction type
- Find reactions by reactants
- Find reactions by products
- Find reactions by catalysts
- Find reactions by dataset source

### Search Procedures

- Retrieve experimental procedures
- Find similar procedures
- Compare procedures

### Analyze Reaction Trends

- Catalyst usage
- Solvent usage
- Temperature distributions
- Yield distributions
- Dataset-level statistics

### Analyze Uploaded Experiments

Users should be able to upload:

- Experimental procedures
- ELN exports
- Reaction plans
- Reports
- Spreadsheets

The system should compare uploaded content against ORD and generate evidence-based observations.

---

# Available Datasets

The repository contains:

dataset/

├── ord_jsonl_v1/
├── ord_procedures_v1/
└── molecule_registry_v1/

These datasets are already complete.

They are the source of truth.

Do NOT:

- Re-download ORD
- Reconvert ORD
- Generate alternate dataset formats

---

## ORD Reactions

Location:

dataset/ord_jsonl_v1

Records:

2,376,120 reactions

Schema Example:

```json
{
  "reaction_id": "...",
  "reaction_type": "...",
  "source_dataset": "...",

  "reactants": [...],
  "reagents": [...],
  "catalysts": [...],
  "products": [...],

  "conditions": {
    "temperature_c": 110.0
  }
}
```

## ORD Procedures

Location:

dataset/ord_procedures_v1

Records:

1,788,170 procedures

Schema Example:

```json
{
  "reaction_id": "...",
  "reaction_type": "...",

  "temperature_c": 150.0,
  "yield_percent": 46.3,

  "procedure_text": "..."
}
```

## Molecule Registry

Location:

dataset/molecule_registry_v1

Records:

1,993,180 molecules

Schema Example:

```json
{
  "smiles": "Cl",
  "occurrences": 233296
}
```

---

# Mandatory First Task

Before implementing any application functionality:

Create a validation script.

The script must verify:

Reactions:
2,376,120

Procedures:
1,788,170

Molecules:
1,993,180

No further work should begin until dataset access is confirmed.

---

# Performance Requirements

The datasets are extremely large.

Never load the full datasets into memory.

Forbidden:

```python
all_reactions = []

for file in files:
    all_reactions.extend(...)
```

Required approach:

```text
JSONL
↓
DuckDB
↓
Queries
```

All production queries should execute through DuckDB.

---

# Technology Stack

## Backend

FastAPI

## Frontend

Next.js

TailwindCSS

shadcn/ui

## Database

DuckDB

## Default Local LLM

Ollama

Default model:

qwen2.5:3b

## Future External Providers

- OpenAI
- Anthropic
- Gemini

---

# System Architecture

User
↓
Chat Interface
↓
Planner
↓
Tool Execution
↓
DuckDB
↓
Analysis Model
↓
Response

The system should use:

Planner + Tools

NOT:

Autonomous agents

---

# Database Architecture

Create:

backend/database/ord.duckdb

Suggested Tables:

## reactions

Columns:

- reaction_id
- reaction_type
- source_dataset
- source_dataset_id
- reactants_json
- reagents_json
- catalysts_json
- products_json
- conditions_json

## procedures

Columns:

- reaction_id
- reaction_type
- temperature_c
- yield_percent
- procedure_text

## molecules

Columns:

- smiles
- occurrences

Chemistry structures should be preserved as JSON whenever possible.

Avoid destructive flattening.

---

# Tool Architecture

Every capability should be implemented as a separate tool.

## search_reactions()

Capabilities:

- reaction type search
- reactant search
- product search
- catalyst search

## search_procedures()

Capabilities:

- retrieve procedures
- retrieve similar procedures

## reaction_statistics()

Capabilities:

- catalyst frequency
- solvent frequency
- temperature distributions
- yield distributions

## molecule_lookup()

Capabilities:

- molecule search
- occurrence statistics

## analyze_uploaded_file()

Capabilities:

- extract text
- identify chemistry information
- compare against ORD
- generate observations

---

# Internal DSL

Use JSON.

Example:

```json
{
  "tool": "search_reactions",
  "filters": {
    "reaction_type": "Buchwald-Hartwig",
    "yield_min": 80
  }
}
```

Do not build a custom language.

JSON is the internal DSL.

---

# LLM Architecture

The application must support multiple providers.

Never hardcode Ollama directly into business logic.

Required structure:

providers/

base.py

ollama_provider.py

openai_provider.py

anthropic_provider.py

gemini_provider.py

All providers must expose a common interface.

Example:

```python
class BaseProvider:

    def chat(self, messages, **kwargs):
        pass

    def generate(self, prompt, **kwargs):
        pass
```

Provider selection should be configurable.

---

# Model Roles

## Planner Model

Responsibilities:

- intent detection
- parameter extraction
- tool selection

Default:

qwen2.5:3b

## Analysis Model

Responsibilities:

- summarization
- experiment comparison
- recommendations
- procedure review

May use:

- Ollama
- GPT
- Claude
- Gemini

Planner and analysis models should be independently configurable.

---

# File Analysis

Supported Upload Types:

- PDF
- DOCX
- TXT
- CSV
- XLSX
- JSON

Workflow:

Upload
↓
Text Extraction
↓
Chemistry Extraction
↓
ORD Retrieval
↓
Comparison
↓
Summary

Example Outputs:

- Similar reactions found
- Typical temperature ranges
- Common catalysts
- Yield statistics
- Procedure comparisons

---

# User Interface

The application should resemble a modern AI chat application.

Required Features:

- Chat interface
- Streaming responses
- File uploads
- Conversation history
- Source references
- Reaction cards
- Procedure cards

The UI should prioritize simplicity and usability.

---

# Development Roadmap

Phase 1

- Dataset validation
- DuckDB ingestion
- Database schema

Phase 2

- Search tools
- Procedure retrieval
- Analytics tools

Phase 3

- FastAPI backend
- Planner implementation
- LLM provider system

Phase 4

- Next.js chat interface
- Streaming responses
- File upload support

Phase 5

- Experiment comparison engine
- Advanced analytics
- External LLM support

---

# Project Memory

The following files must be maintained throughout development:

PROJECT_STATE.md

TASKS.md

DECISIONS.md

AI_HANDOFF.md

Every major milestone must update these files.

Future development may be performed by:

- Codex
- GPT
- Claude
- Gemini

Documentation must remain sufficient for another model to continue development without re-reading the entire codebase.