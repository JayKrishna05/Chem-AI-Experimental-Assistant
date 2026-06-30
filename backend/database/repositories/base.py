from pathlib import Path
from typing import Any
from backend.utils import sanitize_json

class BaseRepository:
    def __init__(self, database_path: str | Path | None = None):
        self.database_path = database_path

    def _fetch_one(self, sql: str, params: list[Any] | None = None) -> dict[str, Any]:
        from backend.tools.db import connect_read_only
        with connect_read_only(self.database_path) as con:
            cursor = con.execute(sql, params or [])
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
        if row:
            return sanitize_json(dict(zip(columns, row, strict=True)))
        return {}

    def _fetch_all(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        from backend.tools.db import connect_read_only
        with connect_read_only(self.database_path) as con:
            cursor = con.execute(sql, params or [])
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
        return [sanitize_json(dict(zip(columns, row, strict=True))) for row in rows]

    def _execute_structured_query(self, sql: str, params: list[Any]) -> tuple[list[str], list[tuple[Any, ...]]]:
        from backend.tools.db import connect_read_only
        with connect_read_only(self.database_path) as con:
            cursor = con.execute(sql, params)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
        return columns, rows

    def _execute_count_query(self, sql: str, params: list[Any]) -> int:
        from backend.tools.db import connect_read_only
        with connect_read_only(self.database_path) as con:
            cursor = con.execute(sql, params)
            row = cursor.fetchone()
        return row[0] if row else 0
