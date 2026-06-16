"""Typed API request and response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database_path: str
    database_available: bool


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
