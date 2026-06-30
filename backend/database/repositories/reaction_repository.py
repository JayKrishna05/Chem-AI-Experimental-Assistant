from backend.tools.filters import build_filters, build_where_sql
import json
from pathlib import Path
from typing import Any, TYPE_CHECKING
from backend.database.repositories.base import BaseRepository

if TYPE_CHECKING:
    from backend.tools.filters import CommonFilters

def _json_load(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value

class ReactionRepository(BaseRepository):
    def search_reactions(self, filters: "CommonFilters", limit: int) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, reaction_alias="reactions")
        where_sql = build_where_sql(where_clauses)
        
        count_sql = f"SELECT COUNT(*) FROM reactions {where_sql}"
        total = self._execute_count_query(count_sql, params)

        params.append(limit)
        sql = f"""
            SELECT
                reaction_id,
                reaction_type,
                source_dataset,
                source_dataset_id,
                reactants_json,
                reagents_json,
                catalysts_json,
                products_json,
                conditions_json
            FROM reactions
            {where_sql}
            ORDER BY reaction_id
            LIMIT ?
        """
        columns, rows = self._execute_structured_query(sql, params)
        json_columns = {
            "reactants_json",
            "reagents_json",
            "catalysts_json",
            "products_json",
            "conditions_json",
        }
        results = []
        for row in rows:
            item = dict(zip(columns, row, strict=True))
            for column in json_columns:
                item[column] = _json_load(item[column])
            results.append(item)

        return results, total

    def search_by_components(
        self,
        reactants: list[str] | None = None,
        products: list[str] | None = None,
        catalysts: list[str] | None = None,
        limit: int = 10
    ) -> tuple[list[dict[str, Any]], int]:
        clauses = []
        params = []
        
        if reactants:
            for r in reactants:
                clauses.append("CAST(reactants_json AS VARCHAR) ILIKE ?")
                params.append(f"%{r}%")
        if products:
            for p in products:
                clauses.append("CAST(products_json AS VARCHAR) ILIKE ?")
                params.append(f"%{p}%")
        if catalysts:
            for c in catalysts:
                clauses.append("CAST(catalysts_json AS VARCHAR) ILIKE ?")
                params.append(f"%{c}%")
                
        where_sql = build_where_sql(clauses)
        
        count_sql = f"SELECT COUNT(*) FROM reactions {where_sql}"
        total = self._execute_count_query(count_sql, params)

        params.append(limit)
        sql = f"""
            SELECT
                reaction_id,
                reaction_type,
                source_dataset,
                source_dataset_id,
                reactants_json,
                reagents_json,
                catalysts_json,
                products_json,
                conditions_json
            FROM reactions
            {where_sql}
            ORDER BY reaction_id
            LIMIT ?
        """
        columns, rows = self._execute_structured_query(sql, params)
        json_columns = {
            "reactants_json",
            "reagents_json",
            "catalysts_json",
            "products_json",
            "conditions_json",
        }
        results = []
        for row in rows:
            item = dict(zip(columns, row, strict=True))
            for column in json_columns:
                item[column] = _json_load(item[column])
            results.append(item)

        return results, total

    def molecule_lookup(self, filters: "CommonFilters", limit: int) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, molecule_alias="molecules")
        where_sql = build_where_sql(where_clauses)
        
        count_sql = f"SELECT COUNT(*) FROM molecules {where_sql}"
        total = self._execute_count_query(count_sql, params)

        params.append(limit)
        sql = f"""
            SELECT smiles, occurrences
            FROM molecules
            {where_sql}
            ORDER BY occurrences DESC, smiles
            LIMIT ?
        """
        columns, rows = self._execute_structured_query(sql, params)
        results = [dict(zip(columns, row, strict=True)) for row in rows]

        return results, total

