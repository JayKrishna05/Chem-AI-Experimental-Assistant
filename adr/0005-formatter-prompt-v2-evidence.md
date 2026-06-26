# ADR 0005: Formatter Prompt V2 & Evidence-First Formatting

**Date:** 2026-06-26
**Status:** Accepted

## Context
During the initial benchmark tests, the Formatter LLM was observed discarding numeric evidence, hallucinating details (e.g., claiming 0% yields instead of acknowledging omitted yields), and formatting tables poorly.

## Decision
We implemented a strict "Evidence-First" prompt constraint (Formatter Prompt V2). The LLM is explicitly instructed to act purely as a data-presentation layer.

## Constraints Applied
- Never hallucinate chemistry constraints not present in the original user prompt.
- Always quote the exact numbers and counts returned by the database.
- Explicitly state when results are truncated.
- Do not perform arithmetic logic on the data.

## Consequences
- **Pros**: Drastically increased reliability and trustworthiness of the agent's output. The system now acts as a natural language bridge to an analytical database, rather than a hallucinating oracle.
- **Cons**: The LLM's tone is somewhat drier and more mechanical. Extrapolation capabilities are intentionally constrained.
