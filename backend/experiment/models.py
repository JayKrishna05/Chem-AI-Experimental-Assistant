"""Canonical schemas for uploaded chemical experiments."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CanonicalExperiment(BaseModel):
    """The canonical representation of any uploaded experiment.
    
    Every supported input (JSON, CSV, text) maps into exactly this internal object.
    """
    experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "unknown"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    schema_version: str = "1.0"

    reaction_type: str | None = None
    reactants: list[str] = Field(default_factory=list)
    reagents: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)

    temperature_c: float | None = None
    yield_percent: float | None = None
    
    # Store raw extraction for debugging or fallback
    raw_text: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of normalizing and validating a CanonicalExperiment."""
    experiment: CanonicalExperiment
    warnings: list[str] = Field(default_factory=list)
    confidence_score: float = 1.0  # 0.0 to 1.0
    normalized_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    is_valid: bool = True  # Usually True unless completely empty/invalid


class UploadMetadata(BaseModel):
    """Metadata for uploaded files for provenance and persistence."""
    upload_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    mime_type: str
    parser_used: str
    parser_version: str = "1.0"
    uploaded_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    parse_duration_ms: float = 0.0
    validation_score: float = 0.0
    warnings: list[str] = Field(default_factory=list)


class EvidenceBundle(BaseModel):
    """Provenance and evidence for scientific claims during comparison."""
    matching_strategy: str = "none"
    representative_reaction_ids: list[str] = Field(default_factory=list)
    dataset_size: int = 0
    sample_size: int = 0
    statistical_method: str = "none"
    assumptions: list[str] = Field(default_factory=list)
    confidence_rationale: str = ""
    query_filters: dict[str, Any] = Field(default_factory=dict)
    excluded_rows: int = 0
    mean: float | None = None
    median: float | None = None
    standard_deviation: float | None = None
    execution_time_ms: float = 0.0


class ComparisonResult(BaseModel):
    """Strongly typed output of the Comparison Service."""
    experiment_id: str
    is_supported: bool = False
    evidence: EvidenceBundle = Field(default_factory=EvidenceBundle)
    
    # Analysis outputs
    yield_classification: str = "Unknown"  # Excellent Match, Comparable, Suboptimal, etc.
    temperature_analysis: str = "Unknown"
    conditions_analysis: str = "Unknown"
    
    # Detailed match information
    literature_matches: int = 0
    literature_yield_avg: float | None = None
    literature_temp_avg: float | None = None

