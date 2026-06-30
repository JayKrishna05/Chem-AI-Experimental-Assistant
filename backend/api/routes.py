"""HTTP routes that delegate to the DuckDB tool layer."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, HTTPException, Query

from backend.api.models import (
    CatalystStatisticsParams,
    CatalystStatisticsResponse,
    DatasetSummaryResponse,
    HealthResponse,
    SystemCapabilitiesResponse,
    MoleculeSearchResponse,
    MoleculeSearchParams,
    ProcedureSearchParams,
    ProcedureSearchResponse,
    ReactionSearchParams,
    ReactionSearchResponse,
    ReactionTypeStatisticsParams,
    ReactionTypeStatisticsResponse,
    SourceDatasetStatisticsParams,
    SourceDatasetStatisticsResponse,
    TemperatureStatisticsParams,
    TemperatureStatisticsResponse,
    YieldStatisticsParams,
    YieldStatisticsResponse,
    ReagentStatisticsParams,
    ReagentStatisticsResponse,
    CompareDatasetsParams,
    CompareDatasetsResponse,
    TopYieldConditionsParams,
    TopYieldConditionsResponse,
    DatasetQualityReportResponse,
)
from backend.tools.analytics_tools import (
    catalyst_statistics,
    dataset_summary,
    reaction_type_statistics,
    reagent_statistics,
    source_dataset_statistics,
    temperature_statistics,
    yield_statistics,
    compare_datasets,
    dataset_quality_report,
    top_yield_conditions,
)
from backend.tools.chemistry_tools import (
    molecule_lookup,
    search_procedures,
    search_reactions,
)
from backend.tools.db import DEFAULT_DB_PATH


router = APIRouter()


def handle_tool_error(exc: Exception) -> None:
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, (ValueError, TypeError)):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, duckdb.Error):
        raise HTTPException(status_code=500, detail="DuckDB query failed") from exc
    raise HTTPException(status_code=500, detail="Unexpected API error") from exc


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    database_available = DEFAULT_DB_PATH.exists()
    return HealthResponse(
        status="ok" if database_available else "degraded",
        database_path=str(DEFAULT_DB_PATH),
        database_available=database_available,
    )

@router.get("/system/capabilities", response_model=SystemCapabilitiesResponse)
def system_capabilities() -> SystemCapabilitiesResponse:
    return SystemCapabilitiesResponse(
        upload_formats=["json", "csv", "xlsx", "text"],
        max_file_size_mb=10,
        features=["experiment_upload", "experiment_comparison"]
    )



@router.get("/reactions/search", response_model=ReactionSearchResponse)
def reactions_search(
    reaction_id: Annotated[str | None, Query()] = None,
    reaction_type: Annotated[str | None, Query()] = None,
    source_dataset: Annotated[str | None, Query()] = None,
    source_dataset_id: Annotated[str | None, Query()] = None,
    reactant: Annotated[str | None, Query()] = None,
    reagent: Annotated[str | None, Query()] = None,
    catalyst: Annotated[str | None, Query()] = None,
    product: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ReactionSearchResponse:
    params = ReactionSearchParams(
        reaction_id=reaction_id,
        reaction_type=reaction_type,
        source_dataset=source_dataset,
        source_dataset_id=source_dataset_id,
        reactant=reactant,
        reagent=reagent,
        catalyst=catalyst,
        product=product,
        limit=limit,
    )
    try:
        payload = search_reactions(**params.model_dump())
        return ReactionSearchResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 - translate tool failures to HTTP.
        handle_tool_error(exc)


@router.get("/procedures/search", response_model=ProcedureSearchResponse)
def procedures_search(
    reaction_id: Annotated[str | None, Query()] = None,
    reaction_type: Annotated[str | None, Query()] = None,
    text: Annotated[str | None, Query()] = None,
    temperature_min: Annotated[float | None, Query()] = None,
    temperature_max: Annotated[float | None, Query()] = None,
    yield_min: Annotated[float | None, Query()] = None,
    yield_max: Annotated[float | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ProcedureSearchResponse:
    params = ProcedureSearchParams(
        reaction_id=reaction_id,
        reaction_type=reaction_type,
        text=text,
        temperature_min=temperature_min,
        temperature_max=temperature_max,
        yield_min=yield_min,
        yield_max=yield_max,
        limit=limit,
    )
    try:
        payload = search_procedures(**params.model_dump())
        return ProcedureSearchResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 - translate tool failures to HTTP.
        handle_tool_error(exc)


@router.get("/molecules/search", response_model=MoleculeSearchResponse)
def molecules_search(
    smiles: Annotated[str | None, Query()] = None,
    query: Annotated[str | None, Query()] = None,
    min_occurrences: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> MoleculeSearchResponse:
    params = MoleculeSearchParams(
        smiles=smiles,
        query=query,
        min_occurrences=min_occurrences,
        limit=limit,
    )
    try:
        payload = molecule_lookup(**params.model_dump())
        return MoleculeSearchResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 - translate tool failures to HTTP.
        handle_tool_error(exc)


# ---------------------------------------------------------------------------
# Analytics endpoints
# ---------------------------------------------------------------------------


@router.get("/analytics/catalysts", response_model=CatalystStatisticsResponse)
def analytics_catalysts(
    reaction_type: Annotated[str | None, Query()] = None,
    source_dataset: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> CatalystStatisticsResponse:
    """Rank catalysts by occurrence and distinct reaction coverage."""
    params = CatalystStatisticsParams(
        reaction_type=reaction_type,
        source_dataset=source_dataset,
        limit=limit,
    )
    try:
        payload = catalyst_statistics(**params.model_dump())
        return CatalystStatisticsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/yields", response_model=YieldStatisticsResponse)
def analytics_yields(
    reaction_type: Annotated[str | None, Query()] = None,
    source_dataset: Annotated[str | None, Query()] = None,
) -> YieldStatisticsResponse:
    """Summarize yield percent distributions for matching procedures."""
    params = YieldStatisticsParams(
        reaction_type=reaction_type,
        source_dataset=source_dataset,
    )
    try:
        payload = yield_statistics(**params.model_dump())
        return YieldStatisticsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/temperatures", response_model=TemperatureStatisticsResponse)
def analytics_temperatures(
    reaction_type: Annotated[str | None, Query()] = None,
    source_dataset: Annotated[str | None, Query()] = None,
) -> TemperatureStatisticsResponse:
    """Summarize temperature distributions in Celsius for matching procedures."""
    params = TemperatureStatisticsParams(
        reaction_type=reaction_type,
        source_dataset=source_dataset,
    )
    try:
        payload = temperature_statistics(**params.model_dump())
        return TemperatureStatisticsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/datasets", response_model=SourceDatasetStatisticsResponse)
def analytics_datasets(
    reaction_type: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str | None, Query()] = "reaction_count",
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> SourceDatasetStatisticsResponse:
    """Summarize reaction and procedure coverage by ORD source dataset."""
    params = SourceDatasetStatisticsParams(
        reaction_type=reaction_type,
        sort_by=sort_by,
        limit=limit,
    )
    try:
        payload = source_dataset_statistics(**params.model_dump())
        return SourceDatasetStatisticsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/reaction-types", response_model=ReactionTypeStatisticsResponse)
def analytics_reaction_types(
    source_dataset: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str | None, Query()] = "reaction_count",
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ReactionTypeStatisticsResponse:
    """Summarize reaction and procedure coverage by reaction type."""
    params = ReactionTypeStatisticsParams(
        source_dataset=source_dataset,
        sort_by=sort_by,
        limit=limit,
    )
    try:
        payload = reaction_type_statistics(**params.model_dump())
        return ReactionTypeStatisticsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/summary", response_model=DatasetSummaryResponse)
def analytics_summary() -> DatasetSummaryResponse:
    """Return high-level dataset coverage counts for the local ORD database."""
    try:
        payload = dataset_summary()
        return DatasetSummaryResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/reagents", response_model=ReagentStatisticsResponse)
def analytics_reagents(
    reaction_type: Annotated[str | None, Query()] = None,
    source_dataset: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ReagentStatisticsResponse:
    """Rank reagents/solvents by occurrence and distinct reaction coverage."""
    params = ReagentStatisticsParams(
        reaction_type=reaction_type,
        source_dataset=source_dataset,
        limit=limit,
    )
    try:
        payload = reagent_statistics(**params.model_dump())
        return ReagentStatisticsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/compare-datasets", response_model=CompareDatasetsResponse)
def analytics_compare_datasets(
    group_by: Annotated[str | None, Query()] = "source_dataset",
    reaction_type: Annotated[str | None, Query()] = None,
    source_dataset: Annotated[str | None, Query()] = None,
    catalyst: Annotated[str | None, Query()] = None,
) -> CompareDatasetsResponse:
    """Compare datasets grouped by reaction_type or source_dataset."""
    params = CompareDatasetsParams(
        group_by=group_by,
        reaction_type=reaction_type,
        source_dataset=source_dataset,
        catalyst=catalyst,
    )
    try:
        payload = compare_datasets(**params.model_dump())
        return CompareDatasetsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/top-yield-conditions", response_model=TopYieldConditionsResponse)
def analytics_top_yield_conditions(
    reaction_type: Annotated[str | None, Query()] = None,
    source_dataset: Annotated[str | None, Query()] = None,
) -> TopYieldConditionsResponse:
    """Find conditions that give the best average yields."""
    params = TopYieldConditionsParams(
        reaction_type=reaction_type,
        source_dataset=source_dataset,
    )
    try:
        payload = top_yield_conditions(**params.model_dump())
        return TopYieldConditionsResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


@router.get("/analytics/quality-report", response_model=DatasetQualityReportResponse)
def analytics_quality_report() -> DatasetQualityReportResponse:
    """Show dataset completeness."""
    try:
        payload = dataset_quality_report()
        return DatasetQualityReportResponse.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        handle_tool_error(exc)


# ---------------------------------------------------------------------------
# Upload & Compare endpoints
# ---------------------------------------------------------------------------

from fastapi import Request, File, UploadFile
import json
from backend.api.models import UploadExperimentRequest, ParseExperimentResponse, CompareExperimentResponse
from backend.experiment.parser import dispatch_parse
from backend.experiment.normalizer import normalize_experiment
from backend.experiment.validator import validate_experiment
from backend.services.comparison_service import compare_experiment


async def _parse_and_validate(request: Request, file: UploadFile | None = None) -> list[Any]:
    content_type = request.headers.get("content-type", "").lower()
    
    exps = []
    
    if "multipart/form-data" in content_type and file:
        data = await file.read()
        exps, _ = dispatch_parse(data, filename=file.filename, mime_type=file.content_type)
    elif "application/json" in content_type:
        body = await request.json()
        req_obj = UploadExperimentRequest(**body)
        
        # Simulate file based on format
        if req_obj.format == "json":
            exps, _ = dispatch_parse(req_obj.content.encode("utf-8"), "upload.json", "application/json")
        elif req_obj.format == "csv":
            exps, _ = dispatch_parse(req_obj.content.encode("utf-8"), "upload.csv", "text/csv")
        else:
            exps, _ = dispatch_parse(req_obj.content.encode("utf-8"), "upload.txt", "text/plain")
    else:
        raise ValueError("Unsupported content type or missing file")
        
    results = []
    for exp in exps:
        normalized_exp, normalized_fields = normalize_experiment(exp)
        validation_result = validate_experiment(normalized_exp, normalized_fields)
        results.append(validation_result)
        
    return results


@router.post("/experiments/parse", response_model=ParseExperimentResponse)
async def experiments_parse(request: Request, file: UploadFile | None = File(None)) -> ParseExperimentResponse:
    """Parse and validate an uploaded experiment payload (supports multipart file uploads and legacy JSON)."""
    try:
        results = await _parse_and_validate(request, file)
        if not results:
            return ParseExperimentResponse(experiments=[], warnings=["No experiments parsed"], is_valid=False)
            
        experiments = [res.experiment.model_dump() for res in results]
        warnings = []
        is_valid = True
        for res in results:
            warnings.extend(res.warnings)
            if not res.is_valid:
                is_valid = False
                
        return ParseExperimentResponse(
            experiments=experiments,
            warnings=list(set(warnings)),
            is_valid=is_valid
        )
    except Exception as exc:
        handle_tool_error(exc)


@router.post("/experiments/compare", response_model=CompareExperimentResponse)
async def experiments_compare(request: Request, file: UploadFile | None = File(None)) -> CompareExperimentResponse:
    """Parse, validate, and compare uploaded experiments against the database (supports multipart file uploads and legacy JSON)."""
    try:
        validation_results = await _parse_and_validate(request, file)
        
        comparisons = []
        for res in validation_results:
            comp_report = compare_experiment(res)
            comparisons.append(comp_report)
            
        return CompareExperimentResponse(comparisons=comparisons)
    except Exception as exc:
        handle_tool_error(exc)
