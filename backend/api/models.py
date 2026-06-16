"""Typed API request and response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database_path: str
    database_available: bool


class ChatRequest(BaseModel):
    message: str
    provider: str | None = None
    model: str | None = None
    formatter_model: str | None = None


class ModelListResponse(BaseModel):
    models: list[str]


class CurrentModelsResponse(BaseModel):
    planner_model: str
    formatter_model: str


class SetModelsRequest(BaseModel):
    planner_model: str | None = None
    formatter_model: str | None = None


class ReactionSearchParams(BaseModel):
    reaction_id: str | None = None
    reaction_type: str | None = None
    source_dataset: str | None = None
    source_dataset_id: str | None = None
    reactant: str | None = None
    reagent: str | None = None
    catalyst: str | None = None
    product: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class ProcedureSearchParams(BaseModel):
    reaction_id: str | None = None
    reaction_type: str | None = None
    text: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    yield_min: float | None = None
    yield_max: float | None = None
    limit: int = Field(default=10, ge=1, le=100)


class MoleculeSearchParams(BaseModel):
    smiles: str | None = None
    query: str | None = None
    min_occurrences: int | None = Field(default=None, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


class ReactionResult(BaseModel):
    reaction_id: str
    reaction_type: str | None = None
    source_dataset: str | None = None
    source_dataset_id: str | None = None
    reactants_json: list[Any] | None = None
    reagents_json: list[Any] | None = None
    catalysts_json: list[Any] | None = None
    products_json: list[Any] | None = None
    conditions_json: dict[str, Any] | None = None


class ProcedureResult(BaseModel):
    reaction_id: str
    reaction_type: str | None = None
    temperature_c: float | None = None
    yield_percent: float | None = None
    procedure_text: str | None = None


class MoleculeResult(BaseModel):
    smiles: str
    occurrences: int | None = None


class ReactionSearchResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    limit: int
    count: int
    results: list[ReactionResult]


class ProcedureSearchResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    limit: int
    count: int
    results: list[ProcedureResult]


class MoleculeSearchResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    limit: int
    count: int
    results: list[MoleculeResult]


class ErrorResponse(BaseModel):
    detail: str


# ---------------------------------------------------------------------------
# Analytics models
# ---------------------------------------------------------------------------


class CatalystStatisticsParams(BaseModel):
    reaction_type: str | None = None
    source_dataset: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class CatalystResult(BaseModel):
    catalyst_smiles: str
    catalyst_name: str
    catalyst_entry_count: int
    reaction_count: int


class CatalystStatisticsResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    limit: int
    count: int
    results: list[CatalystResult]
    assumptions: list[str]


class YieldStatisticsParams(BaseModel):
    reaction_type: str | None = None
    source_dataset: str | None = None


class NumericCoverage(BaseModel):
    total_records: int
    records_with_value: int
    records_with_finite_value: int


class NumericSummary(BaseModel):
    count: int | None = None
    average: float | None = None
    median: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    sample_stddev: float | None = None
    p25: float | None = None
    p75: float | None = None


class YieldQualityChecks(BaseModel):
    below_zero_count: int
    above_hundred_count: int


class YieldStatisticsResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    metric: str
    coverage: NumericCoverage
    statistics: NumericSummary
    assumptions: list[str]
    quality_checks: YieldQualityChecks


class TemperatureStatisticsParams(BaseModel):
    reaction_type: str | None = None
    source_dataset: str | None = None


class TemperatureStatisticsResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    metric: str
    coverage: NumericCoverage
    statistics: NumericSummary
    assumptions: list[str]


class SourceDatasetStatisticsParams(BaseModel):
    reaction_type: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class DatasetCoverageResult(BaseModel):
    source_dataset: str | None = None
    reaction_count: int
    procedure_count: int
    yield_count: int
    temperature_count: int


class SourceDatasetStatisticsResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    limit: int
    count: int
    results: list[DatasetCoverageResult]
    assumptions: list[str]


class ReactionTypeStatisticsParams(BaseModel):
    source_dataset: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class ReactionTypeCoverageResult(BaseModel):
    reaction_type: str | None = None
    reaction_count: int
    procedure_count: int
    yield_count: int
    temperature_count: int


class ReactionTypeStatisticsResponse(BaseModel):
    tool: str
    filters: dict[str, Any]
    limit: int
    count: int
    results: list[ReactionTypeCoverageResult]
    assumptions: list[str]


class DatasetCounts(BaseModel):
    reaction_count: int
    procedure_count: int
    molecule_count: int
    reaction_type_count: int
    source_dataset_count: int


class ReactionCoverage(BaseModel):
    reactions_with_catalysts: int
    reactions_with_products: int
    reactions_with_reactants: int


class ProcedureCoverage(BaseModel):
    procedures_with_yield: int
    procedures_with_finite_yield: int
    procedures_with_temperature: int
    procedures_with_finite_temperature: int


class DatasetSummaryResponse(BaseModel):
    tool: str
    counts: DatasetCounts
    reaction_coverage: ReactionCoverage
    procedure_coverage: ProcedureCoverage
    assumptions: list[str]
