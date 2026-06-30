"""Typed API request and response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database_path: str
    database_available: bool

class SystemCapabilitiesResponse(BaseModel):
    upload_formats: list[str]
    max_file_size_mb: int
    features: list[str]



class ChatRequest(BaseModel):
    message: str
    # Provider and model for the planner role
    planner_provider: str | None = None
    provider: str | None = None  # legacy alias for planner_provider
    model: str | None = None     # planner model
    planner_timeout: float | None = None
    # Provider and model for the formatter role
    formatter_provider: str | None = None
    formatter_model: str | None = None
    formatter_timeout: float | None = None
    # Tool override to bypass planner
    tool_result_override: dict[str, Any] | None = None
    tool_name_override: str | None = None


class ModelListResponse(BaseModel):
    models: list[str]
    available: bool = True
    error: str | None = None


class CurrentModelsResponse(BaseModel):
    planner_provider: str | None = "ollama"
    planner_model: str | None
    planner_timeout: float | None = 59.0
    formatter_provider: str | None = "ollama"
    formatter_model: str | None
    formatter_timeout: float | None = 59.0


class SetModelsRequest(BaseModel):
    planner_provider: str | None = None
    planner_model: str | None = None
    planner_timeout: float | None = None
    formatter_provider: str | None = None
    formatter_model: str | None = None
    formatter_timeout: float | None = None


class StandardResponse(BaseModel):
    tool: str
    contract_version: str
    execution_time_ms: float
    applied_filters: dict[str, Any]
    filters: dict[str, Any]
    limit: int
    count: int
    returned_rows: int
    total_matching_rows: int
    truncated: bool
    assumptions: list[str]


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


class ReactionSearchResponse(StandardResponse):
    results: list[ReactionResult]


class ProcedureSearchResponse(StandardResponse):
    results: list[ProcedureResult]


class MoleculeSearchResponse(StandardResponse):
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


class CatalystStatisticsResponse(StandardResponse):
    results: list[CatalystResult]


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


class YieldStatisticsResponse(StandardResponse):
    metric: str
    coverage: NumericCoverage
    statistics: NumericSummary
    quality_checks: YieldQualityChecks | None = None
    clean_statistics: NumericSummary | None = None


class TemperatureStatisticsParams(BaseModel):
    reaction_type: str | None = None
    source_dataset: str | None = None


class TemperatureStatisticsResponse(StandardResponse):
    metric: str
    coverage: NumericCoverage
    statistics: NumericSummary
    clean_statistics: NumericSummary | None = None


class SourceDatasetStatisticsParams(BaseModel):
    reaction_type: str | None = None
    sort_by: str | None = "reaction_count"
    limit: int = Field(default=10, ge=1, le=100)


class DatasetCoverageResult(BaseModel):
    source_dataset: str | None = None
    reaction_count: int
    procedure_count: int
    yield_count: int
    temperature_count: int


class SourceDatasetStatisticsResponse(StandardResponse):
    results: list[DatasetCoverageResult]


class ReactionTypeStatisticsParams(BaseModel):
    source_dataset: str | None = None
    sort_by: str | None = "reaction_count"
    limit: int = Field(default=10, ge=1, le=100)


class ReactionTypeCoverageResult(BaseModel):
    reaction_type: str | None = None
    reaction_count: int
    procedure_count: int
    yield_count: int
    temperature_count: int


class ReactionTypeStatisticsResponse(StandardResponse):
    results: list[ReactionTypeCoverageResult]


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


class DatasetSummaryResponse(StandardResponse):
    counts: DatasetCounts
    reaction_coverage: ReactionCoverage
    procedure_coverage: ProcedureCoverage


class ReagentStatisticsParams(BaseModel):
    reaction_type: str | None = None
    source_dataset: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class ReagentResult(BaseModel):
    reagent_smiles: str
    reagent_name: str
    reagent_entry_count: int
    reaction_count: int


class ReagentStatisticsResponse(StandardResponse):
    results: list[ReagentResult]


class CompareDatasetsParams(BaseModel):
    group_by: str | None = "source_dataset"
    reaction_type: str | None = None
    source_dataset: str | None = None
    catalyst: str | None = None


class CompareDatasetsResult(BaseModel):
    dataset_name: str
    reaction_count: int
    procedure_count: int
    avg_yield: float
    avg_temperature: float


class CompareDatasetsResponse(StandardResponse):
    results: list[CompareDatasetsResult]


class TopYieldConditionsParams(BaseModel):
    reaction_type: str | None = None
    source_dataset: str | None = None


class TopYieldConditionsResult(BaseModel):
    reaction_type: str | None
    catalyst: str
    freq: int
    avg_yield: float


class TopYieldConditionsResponse(StandardResponse):
    results: list[TopYieldConditionsResult]


class DatasetQualityReportResponse(StandardResponse):
    total_reactions: int
    reactions_with_type: int
    total_procedures: int
    procedures_with_yield: int
    procedures_with_temp: int


# ---------------------------------------------------------------------------
# Upload / Compare models
# ---------------------------------------------------------------------------

class UploadExperimentRequest(BaseModel):
    content: str
    format: str = Field(default="json", description="json, csv, or text")


class ParseExperimentResponse(BaseModel):
    experiments: list[Any]
    warnings: list[str]
    is_valid: bool


class CompareExperimentResponse(BaseModel):
    comparisons: list[Any]
