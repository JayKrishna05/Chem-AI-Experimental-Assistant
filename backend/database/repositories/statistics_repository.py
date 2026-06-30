from backend.tools.filters import build_filters, build_where_sql
from typing import Any, TYPE_CHECKING
from backend.database.repositories.base import BaseRepository

if TYPE_CHECKING:
    from backend.tools.filters import CommonFilters

class StatisticsRepository(BaseRepository):
    def get_numeric_statistics(self, table_expression: str, value_column: str, where_clauses: list[str], params: list[Any]) -> dict[str, Any]:
        valid_clause = f"{value_column} IS NOT NULL AND isfinite({value_column})"
        where_sql = build_where_sql([*where_clauses, valid_clause])
        all_where_sql = build_where_sql(where_clauses)

        summary = self._fetch_one(
            f"""
            SELECT
                COUNT(*) AS count,
                AVG({value_column}) AS average,
                MEDIAN({value_column}) AS median,
                MIN({value_column}) AS minimum,
                MAX({value_column}) AS maximum,
                STDDEV_SAMP({value_column}) AS sample_stddev,
                quantile_cont({value_column}, 0.25) AS p25,
                quantile_cont({value_column}, 0.75) AS p75
            FROM {table_expression}
            {where_sql}
            """,
            params,
        )
        coverage = self._fetch_one(
            f"""
            SELECT
                COUNT(*) AS total_records,
                COUNT({value_column}) AS records_with_value,
                COALESCE(SUM(
                    CASE
                        WHEN {value_column} IS NOT NULL AND isfinite({value_column})
                        THEN 1
                        ELSE 0
                    END
                ), 0) AS records_with_finite_value
            FROM {table_expression}
            {all_where_sql}
            """,
            params,
        )
        return {"statistics": summary, "coverage": coverage}

    def get_catalyst_statistics(self, filters: "CommonFilters", limit: int) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, reaction_alias="r")
        where_clauses.append("r.catalysts_json IS NOT NULL")
        where_clauses.append("json_array_length(r.catalysts_json) > 0")
        where_sql = build_where_sql(where_clauses)
        
        count_res = self._fetch_one(
            f"""
            SELECT COUNT(*) as c FROM (
                SELECT 1
                FROM reactions AS r, json_each(r.catalysts_json) AS c
                {where_sql}
                GROUP BY COALESCE(json_extract_string(c.value, '$.smiles'), ''),
                         COALESCE(json_extract_string(c.value, '$.name'), '')
                HAVING COALESCE(json_extract_string(c.value, '$.smiles'), '') <> '' OR
                       COALESCE(json_extract_string(c.value, '$.name'), '') <> ''
            )
            """,
            params,
        )
        total = count_res.get("c", 0) if count_res else 0
        
        params.append(limit)
        results = self._fetch_all(
            f"""
            SELECT
                COALESCE(json_extract_string(c.value, '$.smiles'), '') AS catalyst_smiles,
                COALESCE(json_extract_string(c.value, '$.name'), '') AS catalyst_name,
                COUNT(*) AS catalyst_entry_count,
                COUNT(DISTINCT r.reaction_id) AS reaction_count
            FROM reactions AS r, json_each(r.catalysts_json) AS c
            {where_sql}
            GROUP BY catalyst_smiles, catalyst_name
            HAVING catalyst_smiles <> '' OR catalyst_name <> ''
            ORDER BY reaction_count DESC, catalyst_entry_count DESC, catalyst_smiles, catalyst_name
            LIMIT ?
            """,
            params,
        )
        return results, total

    def get_yield_statistics(self, filters: "CommonFilters") -> dict[str, Any]:
        table_expression = "procedures AS p JOIN reactions AS r ON r.reaction_id = p.reaction_id"
        where_clauses, params = build_filters(filters, reaction_alias="r", procedure_alias="p")

        payload = self.get_numeric_statistics(table_expression, "p.yield_percent", where_clauses, params.copy())
        
        payload["quality_checks"] = self._fetch_one(
            f"""
            SELECT
                COALESCE(SUM(CASE WHEN p.yield_percent < 0 THEN 1 ELSE 0 END), 0)
                    AS below_zero_count,
                COALESCE(SUM(CASE WHEN p.yield_percent > 100 THEN 1 ELSE 0 END), 0)
                    AS above_hundred_count,
                COALESCE(SUM(CASE WHEN p.yield_percent BETWEEN 0 AND 100 THEN 1 ELSE 0 END), 0)
                    AS valid_range_count
            FROM {table_expression}
            {build_where_sql([*where_clauses, 'p.yield_percent IS NOT NULL AND isfinite(p.yield_percent)'])}
            """,
            params,
        )
        
        valid_where = build_where_sql([*where_clauses, "p.yield_percent >= 0", "p.yield_percent <= 100"])
        payload["clean_statistics"] = self._fetch_one(
            f"""
            SELECT
                COUNT(*) AS count,
                AVG(p.yield_percent) AS average,
                MEDIAN(p.yield_percent) AS median,
                MIN(p.yield_percent) AS minimum,
                MAX(p.yield_percent) AS maximum,
                STDDEV_SAMP(p.yield_percent) AS sample_stddev,
                quantile_cont(p.yield_percent, 0.25) AS p25,
                quantile_cont(p.yield_percent, 0.75) AS p75
            FROM {table_expression}
            {valid_where}
            """,
            params,
        )
        return payload

    def get_temperature_statistics(self, filters: "CommonFilters") -> dict[str, Any]:
        table_expression = "procedures AS p JOIN reactions AS r ON r.reaction_id = p.reaction_id"
        where_clauses, params = build_filters(filters, reaction_alias="r", procedure_alias="p")

        payload = self.get_numeric_statistics(table_expression, "p.temperature_c", where_clauses, params.copy())
        
        valid_where = build_where_sql([*where_clauses, "p.temperature_c >= -100", "p.temperature_c <= 300"])
        payload["clean_statistics"] = self._fetch_one(
            f"""
            SELECT
                COUNT(*) AS count,
                AVG(p.temperature_c) AS average,
                MEDIAN(p.temperature_c) AS median,
                MIN(p.temperature_c) AS minimum,
                MAX(p.temperature_c) AS maximum,
                STDDEV_SAMP(p.temperature_c) AS sample_stddev,
                quantile_cont(p.temperature_c, 0.25) AS p25,
                quantile_cont(p.temperature_c, 0.75) AS p75
            FROM {table_expression}
            {valid_where}
            """,
            params,
        )
        return payload

    def get_source_dataset_statistics(self, filters: "CommonFilters", sort_by: str, limit: int) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, reaction_alias="r")
        where_sql = build_where_sql(where_clauses)
        
        count_res = self._fetch_one(
            f"""
            SELECT COUNT(DISTINCT r.source_dataset) as c
            FROM reactions AS r
            {where_sql}
            """,
            params,
        )
        total = count_res.get("c", 0) if count_res else 0
        
        params.append(limit)
        results = self._fetch_all(
            f"""
            WITH procedure_counts AS (
                SELECT
                    reaction_id,
                    COUNT(*) AS procedure_count,
                    COUNT(yield_percent) AS yield_count,
                    COUNT(temperature_c) AS temperature_count
                FROM procedures
                GROUP BY reaction_id
            )
            SELECT
                r.source_dataset,
                COUNT(*) AS reaction_count,
                COALESCE(SUM(pc.procedure_count), 0) AS procedure_count,
                COALESCE(SUM(pc.yield_count), 0) AS yield_count,
                COALESCE(SUM(pc.temperature_count), 0) AS temperature_count
            FROM reactions AS r
            LEFT JOIN procedure_counts AS pc ON pc.reaction_id = r.reaction_id
            {where_sql}
            GROUP BY r.source_dataset
            ORDER BY {sort_by} DESC, r.source_dataset
            LIMIT ?
            """,
            params,
        )
        return results, total

    def get_reaction_type_statistics(self, filters: "CommonFilters", sort_by: str, limit: int) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, reaction_alias="r")
        where_sql = build_where_sql(where_clauses)
        
        count_res = self._fetch_one(
            f"""
            SELECT COUNT(DISTINCT r.reaction_type) as c
            FROM reactions AS r
            {where_sql}
            """,
            params,
        )
        total = count_res.get("c", 0) if count_res else 0
        
        params.append(limit)
        results = self._fetch_all(
            f"""
            WITH procedure_counts AS (
                SELECT
                    reaction_id,
                    COUNT(*) AS procedure_count,
                    COUNT(yield_percent) AS yield_count,
                    COUNT(temperature_c) AS temperature_count
                FROM procedures
                GROUP BY reaction_id
            )
            SELECT
                r.reaction_type,
                COUNT(*) AS reaction_count,
                COALESCE(SUM(pc.procedure_count), 0) AS procedure_count,
                COALESCE(SUM(pc.yield_count), 0) AS yield_count,
                COALESCE(SUM(pc.temperature_count), 0) AS temperature_count
            FROM reactions AS r
            LEFT JOIN procedure_counts AS pc ON pc.reaction_id = r.reaction_id
            {where_sql}
            GROUP BY r.reaction_type
            ORDER BY {sort_by} DESC, r.reaction_type
            LIMIT ?
            """,
            params,
        )
        return results, total

    def get_dataset_summary(self) -> dict[str, Any]:
        counts = self._fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM reactions) AS reaction_count,
                (SELECT COUNT(*) FROM procedures) AS procedure_count,
                (SELECT COUNT(*) FROM molecules) AS molecule_count,
                (SELECT COUNT(DISTINCT reaction_type) FROM reactions) AS reaction_type_count,
                (SELECT COUNT(DISTINCT source_dataset) FROM reactions) AS source_dataset_count
            """
        )
        coverage = self._fetch_one(
            """
            SELECT
                SUM(CASE WHEN json_array_length(catalysts_json) > 0 THEN 1 ELSE 0 END)
                    AS reactions_with_catalysts,
                SUM(CASE WHEN json_array_length(products_json) > 0 THEN 1 ELSE 0 END)
                    AS reactions_with_products,
                SUM(CASE WHEN json_array_length(reactants_json) > 0 THEN 1 ELSE 0 END)
                    AS reactions_with_reactants
            FROM reactions
            """
        )
        procedure_coverage = self._fetch_one(
            """
            SELECT
                COUNT(yield_percent) AS procedures_with_yield,
                SUM(
                    CASE
                        WHEN yield_percent IS NOT NULL AND isfinite(yield_percent)
                        THEN 1
                        ELSE 0
                    END
                ) AS procedures_with_finite_yield,
                COUNT(temperature_c) AS procedures_with_temperature,
                SUM(
                    CASE
                        WHEN temperature_c IS NOT NULL AND isfinite(temperature_c)
                        THEN 1
                        ELSE 0
                    END
                ) AS procedures_with_finite_temperature
            FROM procedures
            """
        )
        return {
            "counts": counts,
            "reaction_coverage": coverage,
            "procedure_coverage": procedure_coverage,
        }

    def get_reagent_statistics(self, filters: "CommonFilters", limit: int) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, reaction_alias="r")
        where_clauses.append("r.reagents_json IS NOT NULL")
        where_clauses.append("json_array_length(r.reagents_json) > 0")
        where_sql = build_where_sql(where_clauses)
        
        count_res = self._fetch_one(
            f"""
            SELECT COUNT(*) as c FROM (
                SELECT 1
                FROM reactions AS r, json_each(r.reagents_json) AS rg
                {where_sql}
                GROUP BY COALESCE(json_extract_string(rg.value, '$.smiles'), ''),
                         COALESCE(json_extract_string(rg.value, '$.name'), '')
                HAVING COALESCE(json_extract_string(rg.value, '$.smiles'), '') <> '' OR
                       COALESCE(json_extract_string(rg.value, '$.name'), '') <> ''
            )
            """,
            params,
        )
        total = count_res.get("c", 0) if count_res else 0
        
        params.append(limit)
        results = self._fetch_all(
            f"""
            SELECT
                COALESCE(json_extract_string(rg.value, '$.smiles'), '') AS reagent_smiles,
                COALESCE(json_extract_string(rg.value, '$.name'), '') AS reagent_name,
                COUNT(*) AS reagent_entry_count,
                COUNT(DISTINCT r.reaction_id) AS reaction_count
            FROM reactions AS r, json_each(r.reagents_json) AS rg
            {where_sql}
            GROUP BY reagent_smiles, reagent_name
            HAVING reagent_smiles <> '' OR reagent_name <> ''
            ORDER BY reaction_count DESC, reagent_entry_count DESC, reagent_smiles, reagent_name
            LIMIT ?
            """,
            params,
        )
        return results, total

    def get_compare_datasets(self, filters: "CommonFilters", group_by: str) -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, reaction_alias="r")
        where_clauses.append(f"r.{group_by} IS NOT NULL")
        where_clauses.append(f"r.{group_by} != ''")
        where_sql = build_where_sql(where_clauses)

        count_res = self._fetch_one(
            f"""
            SELECT COUNT(DISTINCT r.{group_by}) as c
            FROM reactions AS r
            {where_sql}
            """,
            params,
        )
        total = count_res.get("c", 0) if count_res else 0

        results = self._fetch_all(
            f"""
            WITH procedure_counts AS (
                SELECT
                    reaction_id,
                    COUNT(*) AS procedure_count,
                    COUNT(yield_percent) AS yield_count,
                    AVG(yield_percent) AS avg_yield,
                    AVG(temperature_c) AS avg_temperature
                FROM procedures
                GROUP BY reaction_id
            )
            SELECT
                r.{group_by} AS dataset_name,
                COUNT(DISTINCT r.reaction_id) AS reaction_count,
                COALESCE(SUM(pc.procedure_count), 0) AS procedure_count,
                COALESCE(AVG(pc.avg_yield), 0) AS avg_yield,
                COALESCE(AVG(pc.avg_temperature), 0) AS avg_temperature
            FROM reactions AS r
            LEFT JOIN procedure_counts AS pc ON pc.reaction_id = r.reaction_id
            {where_sql}
            GROUP BY r.{group_by}
            ORDER BY reaction_count DESC
            LIMIT 50
            """,
            params,
        )
        return results, total

    def get_top_yield_conditions(self, filters: "CommonFilters") -> tuple[list[dict[str, Any]], int]:
        where_clauses, params = build_filters(filters, reaction_alias="r", procedure_alias="p")
        
        # but what do we group by? We need to group by the query parameters.
        # Let's keep the existing grouping but relax the null constraint, or group by structural features.
        # Actually, let's group by `catalyst` and not `reaction_type` if `reaction_type` isn't provided.
        # Let's group by catalyst only.
        
        grouping_col = "r.reaction_type, c.catalyst"
        
        where_clauses.append("p.yield_percent IS NOT NULL")
        where_sql = build_where_sql(where_clauses)
        
        count_res = self._fetch_one(
            f"""
            SELECT COUNT(*) as c FROM (
                SELECT 1
                FROM reactions r
                JOIN procedures p ON r.reaction_id = p.reaction_id
                JOIN (
                  SELECT reaction_id, unnest(from_json(catalysts_json, '["VARCHAR"]')) as catalyst 
                  FROM reactions
                  WHERE catalysts_json IS NOT NULL AND json_array_length(catalysts_json) > 0
                ) c ON c.reaction_id = r.reaction_id
                {where_sql}
                GROUP BY {grouping_col}
                HAVING COUNT(*) >= 5
            )
            """,
            params,
        )
        total = count_res.get("c", 0) if count_res else 0
        
        results = self._fetch_all(
            f"""
            SELECT 
                r.reaction_type,
                c.catalyst as catalyst,
                COUNT(*) as freq,
                AVG(p.yield_percent) as avg_yield,
                STDDEV_SAMP(p.yield_percent) as stddev_yield
            FROM reactions r
            JOIN procedures p ON r.reaction_id = p.reaction_id
            JOIN (
              SELECT reaction_id, unnest(from_json(catalysts_json, '["VARCHAR"]')) as catalyst 
              FROM reactions
              WHERE catalysts_json IS NOT NULL AND json_array_length(catalysts_json) > 0
            ) c ON c.reaction_id = r.reaction_id
            {where_sql}
            GROUP BY {grouping_col}
            HAVING COUNT(*) >= 5
            ORDER BY avg_yield DESC
            LIMIT 20
            """,
            params,
        )
        return results, total

    def get_dataset_quality_report(self) -> dict[str, Any]:
        return self._fetch_one(
            """
            SELECT
                COUNT(r.reaction_id) as total_reactions,
                SUM(CASE WHEN r.reaction_type IS NOT NULL THEN 1 ELSE 0 END) as reactions_with_type,
                COUNT(p.reaction_id) as total_procedures,
                SUM(CASE WHEN p.yield_percent IS NOT NULL THEN 1 ELSE 0 END) as procedures_with_yield,
                SUM(CASE WHEN p.temperature_c IS NOT NULL THEN 1 ELSE 0 END) as procedures_with_temp
            FROM reactions r
            LEFT JOIN procedures p ON r.reaction_id = p.reaction_id
            """
        )

