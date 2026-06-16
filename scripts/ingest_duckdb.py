"""Create and populate the local ORD DuckDB database from existing JSONL datasets."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb

from validate_datasets import DATASETS, print_report, validate_dataset


DEFAULT_DATABASE_PATH = Path("backend") / "database" / "ord.duckdb"
SCHEMA_PATH = Path("backend") / "database" / "schema.sql"


def sql_literal(value: Path | str) -> str:
    return "'" + str(value).replace("\\", "/").replace("'", "''") + "'"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ORD datasets and ingest them into DuckDB."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root containing dataset and backend directories.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="DuckDB database path, relative to --root unless absolute.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing DuckDB database file before ingesting.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=max(1, (os.cpu_count() or 2) - 1),
        help="DuckDB worker threads to use during ingestion.",
    )
    return parser.parse_args()


def resolve_under_root(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def validate_or_exit(root: Path) -> None:
    results = [validate_dataset(root, spec) for spec in DATASETS]
    print_report(results)
    if not all(result.ok for result in results):
        raise SystemExit("Dataset validation failed; ingestion aborted.")


def execute_schema(con: duckdb.DuckDBPyConnection, root: Path) -> None:
    schema_file = root / SCHEMA_PATH
    con.execute(schema_file.read_text(encoding="utf-8"))


def ingest_reactions(con: duckdb.DuckDBPyConnection, root: Path) -> None:
    source_glob = root / "dataset" / "ord_jsonl_v1" / "*.jsonl"
    con.execute(
        f"""
        INSERT INTO reactions (
            reaction_id,
            reaction_type,
            source_dataset,
            source_dataset_id,
            reactants_json,
            reagents_json,
            catalysts_json,
            products_json,
            conditions_json
        )
        SELECT
            reaction_id,
            reaction_type,
            source_dataset,
            source_dataset_id,
            reactants,
            reagents,
            catalysts,
            products,
            conditions
        FROM read_json(
            {sql_literal(source_glob)},
            format='newline_delimited',
            columns={{
                reaction_id: 'VARCHAR',
                reaction_type: 'VARCHAR',
                source_dataset: 'VARCHAR',
                source_dataset_id: 'VARCHAR',
                reactants: 'JSON',
                reagents: 'JSON',
                catalysts: 'JSON',
                products: 'JSON',
                conditions: 'JSON'
            }}
        );
        """
    )


def ingest_procedures(con: duckdb.DuckDBPyConnection, root: Path) -> None:
    source_glob = root / "dataset" / "ord_procedures_v1" / "*.jsonl"
    con.execute(
        f"""
        INSERT INTO procedures (
            reaction_id,
            reaction_type,
            temperature_c,
            yield_percent,
            procedure_text
        )
        SELECT
            reaction_id,
            reaction_type,
            temperature_c,
            yield_percent,
            procedure_text
        FROM read_json(
            {sql_literal(source_glob)},
            format='newline_delimited',
            columns={{
                reaction_id: 'VARCHAR',
                reaction_type: 'VARCHAR',
                temperature_c: 'DOUBLE',
                yield_percent: 'DOUBLE',
                procedure_text: 'VARCHAR'
            }}
        );
        """
    )


def ingest_molecules(con: duckdb.DuckDBPyConnection, root: Path) -> None:
    source_file = root / "dataset" / "molecule_registry_v1" / "molecules.jsonl"
    con.execute(
        f"""
        INSERT INTO molecules (smiles, occurrences)
        SELECT smiles, occurrences
        FROM read_json(
            {sql_literal(source_file)},
            format='newline_delimited',
            columns={{
                smiles: 'VARCHAR',
                occurrences: 'BIGINT'
            }}
        );
        """
    )


def assert_count(
    con: duckdb.DuckDBPyConnection,
    table: str,
    expected_count: int,
) -> int:
    actual_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if actual_count != expected_count:
        msg = f"{table} imported {actual_count:,} rows; expected {expected_count:,}"
        raise RuntimeError(msg)
    return actual_count


def write_audit_rows(con: duckdb.DuckDBPyConnection, root: Path) -> None:
    specs_by_name = {spec.name: spec for spec in DATASETS}
    rows = (
        (
            "Reactions",
            str(root / specs_by_name["Reactions"].relative_dir),
            specs_by_name["Reactions"].expected_count,
            assert_count(con, "reactions", specs_by_name["Reactions"].expected_count),
        ),
        (
            "Procedures",
            str(root / specs_by_name["Procedures"].relative_dir),
            specs_by_name["Procedures"].expected_count,
            assert_count(
                con,
                "procedures",
                specs_by_name["Procedures"].expected_count,
            ),
        ),
        (
            "Molecules",
            str(root / specs_by_name["Molecules"].relative_dir),
            specs_by_name["Molecules"].expected_count,
            assert_count(con, "molecules", specs_by_name["Molecules"].expected_count),
        ),
    )
    con.executemany(
        """
        INSERT INTO ingestion_audit (
            dataset,
            source_path,
            expected_count,
            imported_count
        )
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )


def create_indexes(con: duckdb.DuckDBPyConnection) -> None:
    index_statements = (
        "CREATE INDEX idx_reactions_reaction_id ON reactions(reaction_id)",
        "CREATE INDEX idx_reactions_reaction_type ON reactions(reaction_type)",
        "CREATE INDEX idx_reactions_source_dataset ON reactions(source_dataset)",
        "CREATE INDEX idx_procedures_reaction_id ON procedures(reaction_id)",
        "CREATE INDEX idx_procedures_reaction_type ON procedures(reaction_type)",
        "CREATE INDEX idx_molecules_smiles ON molecules(smiles)",
    )
    for statement in index_statements:
        con.execute(statement)


def ingest_database(root: Path, database_path: Path, replace: bool, threads: int) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    if database_path.exists():
        if not replace:
            raise SystemExit(
                f"Database already exists: {database_path}. "
                "Use --replace to rebuild it from source datasets."
            )
        database_path.unlink()

    con = duckdb.connect(str(database_path))
    try:
        con.execute(f"PRAGMA threads={max(1, threads)}")
        con.execute("BEGIN TRANSACTION")
        execute_schema(con, root)

        print("Ingesting reactions...")
        ingest_reactions(con, root)

        print("Ingesting procedures...")
        ingest_procedures(con, root)

        print("Ingesting molecules...")
        ingest_molecules(con, root)

        write_audit_rows(con, root)

        print("Creating indexes...")
        create_indexes(con)

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    database_path = resolve_under_root(root, args.database).resolve()

    validate_or_exit(root)
    ingest_database(root, database_path, args.replace, args.threads)

    print(f"DuckDB ingestion succeeded: {database_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
