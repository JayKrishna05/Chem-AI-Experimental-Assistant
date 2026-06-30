from backend.tools.filters import build_filters, build_where_sql
from pathlib import Path
from typing import Any
from backend.database.repositories.base import BaseRepository
from backend.tools.filters import CommonFilters, build_filters, build_where_sql

class ProcedureRepository(BaseRepository):
    def search_procedures(self, filters: "CommonFilters", limit: int) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(
            filters, 
            reaction_alias="procedures", 
            procedure_alias="procedures"
        )
        where_sql = build_where_sql(where_clauses)
        
        count_sql = f"SELECT COUNT(*) FROM procedures {where_sql}"
        total = self._execute_count_query(count_sql, params)

        params.append(limit)
        sql = f"""
            SELECT
                reaction_id,
                reaction_type,
                temperature_c,
                yield_percent,
                procedure_text
            FROM procedures
            {where_sql}
            ORDER BY reaction_id
            LIMIT ?
        """
        columns, rows = self._execute_structured_query(sql, params)
        results = [dict(zip(columns, row, strict=True)) for row in rows]

        return results, total

