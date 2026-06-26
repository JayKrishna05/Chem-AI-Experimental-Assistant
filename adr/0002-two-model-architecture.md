# ADR 0002: Two-Model Architecture

**Date:** 2026-06-26
**Status:** Accepted

## Context
The system must parse complex user intents (e.g., "What is the average yield of Suzuki couplings using Palladium?"), map those to deterministic SQL tools, execute them, and format the response intelligently. A single monolithic LLM prompt struggles to handle complex routing, structured extraction, and unstructured summarization simultaneously without hallucinating schema fields or dropping constraints.

## Decision
We implemented a **Two-Model Architecture**:
1. **Planner Model (Local/Fast)**: Parses the user's intent into strict JSON tool-calls. This model never sees the database payload.
2. **Formatter Model (Groq/Llama-3-70B)**: Takes the raw data (the Evidence Bundle) returned by the DuckDB tools and the original user intent, then generates the final human-readable markdown response.

## Alternatives Considered
- **Single-Model Agent (ReAct)**: Too prone to context-window bloating and hallucination on large chemistry datasets. Slow and expensive for a production deployment.
- **Rules-Based Formatting**: Rigid and incapable of synthesizing novel insights (e.g., explaining why a yield is anomalous).

## Consequences
- **Pros**: Clean separation of concerns. The planner focuses strictly on deterministic data extraction. The formatter focuses purely on language generation.
- **Cons**: Increased system complexity (two distinct LLM passes per request), higher latency.
