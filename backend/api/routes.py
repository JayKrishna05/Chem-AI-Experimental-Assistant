"""HTTP routes that delegate to the DuckDB tool layer."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, HTTPException, Query

from backend.api.models import (
    HealthResponse,
    MoleculeSearchResponse,
    MoleculeSearchParams,
    ProcedureSearchParams,
    ProcedureSearchResponse,
    ReactionSearchParams,
    ReactionSearchResponse,
)
from backend.tools import molecule_lookup, search_procedures, search_reactions
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
