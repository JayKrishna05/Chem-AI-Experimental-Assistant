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
)
from backend.tools import (
    catalyst_statistics,
    dataset_summary,
    molecule_lookup,
    reaction_type_statistics,
    search_procedures,
    search_reactions,
    source_dataset_statistics,
    temperature_statistics,
    yield_statistics,
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
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> SourceDatasetStatisticsResponse:
    """Summarize reaction and procedure coverage by ORD source dataset."""
    params = SourceDatasetStatisticsParams(
        reaction_type=reaction_type,
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
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ReactionTypeStatisticsResponse:
    """Summarize reaction and procedure coverage by reaction type."""
    params = ReactionTypeStatisticsParams(
        source_dataset=source_dataset,
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
