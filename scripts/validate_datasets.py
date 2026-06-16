"""Validate local ORD dataset folders without loading records into memory."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_REACTIONS = 2_376_120
EXPECTED_PROCEDURES = 1_788_170
EXPECTED_MOLECULES = 1_993_180

CHUNK_SIZE = 1024 * 1024 * 8


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    relative_dir: Path
    expected_count: int
    metadata_count_key: str
    required_keys: tuple[str, ...]
    file_pattern: str = "*.jsonl"


@dataclass
class DatasetResult:
    name: str
    path: Path
    expected_count: int
    metadata_count: int | None
    actual_count: int
    files: int
    ok: bool
    messages: list[str]


DATASETS = (
    DatasetSpec(
        name="Reactions",
        relative_dir=Path("dataset") / "ord_jsonl_v1",
        expected_count=EXPECTED_REACTIONS,
        metadata_count_key="total_reactions",
        required_keys=(
            "reaction_id",
            "reaction_type",
            "source_dataset",
            "reactants",
            "reagents",
            "catalysts",
            "products",
            "conditions",
        ),
    ),
    DatasetSpec(
        name="Procedures",
        relative_dir=Path("dataset") / "ord_procedures_v1",
        expected_count=EXPECTED_PROCEDURES,
        metadata_count_key="total_procedures",
        required_keys=("reaction_id", "reaction_type", "procedure_text"),
    ),
    DatasetSpec(
        name="Molecules",
        relative_dir=Path("dataset") / "molecule_registry_v1",
        expected_count=EXPECTED_MOLECULES,
        metadata_count_key="unique_molecules",
        required_keys=("smiles", "occurrences"),
    ),
)


def count_jsonl_records(path: Path) -> int:
    """Count JSONL records by scanning bytes in chunks."""
    count = 0
    saw_bytes = False
    last_byte = b""

    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            saw_bytes = True
            count += chunk.count(b"\n")
            last_byte = chunk[-1:]

    if saw_bytes and last_byte != b"\n":
        count += 1

    return count


def load_metadata(dataset_dir: Path) -> dict[str, Any]:
    metadata_path = dataset_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing metadata file: {metadata_path}")
    with metadata_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_first_record(jsonl_path: Path) -> dict[str, Any]:
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                record = json.loads(stripped)
                if not isinstance(record, dict):
                    raise ValueError(f"First record is not an object in {jsonl_path}")
                return record
    raise ValueError(f"No records found in {jsonl_path}")


def validate_dataset(root: Path, spec: DatasetSpec) -> DatasetResult:
    dataset_dir = root / spec.relative_dir
    messages: list[str] = []
    ok = True

    if not dataset_dir.exists():
        return DatasetResult(
            name=spec.name,
            path=dataset_dir,
            expected_count=spec.expected_count,
            metadata_count=None,
            actual_count=0,
            files=0,
            ok=False,
            messages=[f"missing dataset directory: {dataset_dir}"],
        )

    metadata_count: int | None = None
    try:
        metadata = load_metadata(dataset_dir)
        raw_metadata_count = metadata.get(spec.metadata_count_key)
        if isinstance(raw_metadata_count, int):
            metadata_count = raw_metadata_count
        else:
            ok = False
            messages.append(f"metadata missing integer key: {spec.metadata_count_key}")
    except Exception as exc:  # noqa: BLE001 - report validation failures cleanly.
        ok = False
        messages.append(str(exc))

    if metadata_count != spec.expected_count:
        ok = False
        messages.append(
            f"metadata count {metadata_count!r} does not match expected {spec.expected_count}"
        )

    jsonl_files = sorted(dataset_dir.glob(spec.file_pattern))
    if not jsonl_files:
        return DatasetResult(
            name=spec.name,
            path=dataset_dir,
            expected_count=spec.expected_count,
            metadata_count=metadata_count,
            actual_count=0,
            files=0,
            ok=False,
            messages=messages + ["no JSONL files found"],
        )

    try:
        first_record = read_first_record(jsonl_files[0])
        missing_keys = [key for key in spec.required_keys if key not in first_record]
        if missing_keys:
            ok = False
            messages.append(f"first record missing keys: {', '.join(missing_keys)}")
    except Exception as exc:  # noqa: BLE001 - report validation failures cleanly.
        ok = False
        messages.append(str(exc))

    actual_count = 0
    for jsonl_file in jsonl_files:
        actual_count += count_jsonl_records(jsonl_file)

    if actual_count != spec.expected_count:
        ok = False
        messages.append(
            f"record count {actual_count} does not match expected {spec.expected_count}"
        )

    return DatasetResult(
        name=spec.name,
        path=dataset_dir,
        expected_count=spec.expected_count,
        metadata_count=metadata_count,
        actual_count=actual_count,
        files=len(jsonl_files),
        ok=ok,
        messages=messages,
    )


def format_count(value: int | None) -> str:
    if value is None:
        return "missing"
    return f"{value:,}"


def print_report(results: list[DatasetResult]) -> None:
    print("Dataset validation report")
    print("=========================")
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{result.name}: {status}")
        print(f"  Path: {result.path}")
        print(f"  Files: {result.files}")
        print(f"  Expected: {result.expected_count:,}")
        print(f"  Metadata: {format_count(result.metadata_count)}")
        print(f"  Counted: {result.actual_count:,}")
        for message in result.messages:
            print(f"  - {message}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate expected ORD JSONL datasets and record counts."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root containing the dataset directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    results = [validate_dataset(root, spec) for spec in DATASETS]
    print_report(results)

    if all(result.ok for result in results):
        print("Validation succeeded.")
        return 0

    print("Validation failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
