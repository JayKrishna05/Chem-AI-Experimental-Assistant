"""Shared DuckDB connection helpers for tool modules."""

from __future__ import annotations

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "backend" / "database" / "ord.duckdb"


def resolve_database_path(database_path: str | Path | None = None) -> Path:
    if database_path is None:
        return DEFAULT_DB_PATH

    path = Path(database_path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def connect_read_only(database_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    path = resolve_database_path(database_path)
    if not path.exists():
        raise FileNotFoundError(f"DuckDB database not found: {path}")
    return duckdb.connect(str(path), read_only=True)
