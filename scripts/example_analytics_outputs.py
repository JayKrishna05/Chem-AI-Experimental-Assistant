"""Print compact example outputs from the chemistry analytics tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.tools.analytics_tools import (  # noqa: E402
    catalyst_statistics,
    dataset_summary,
    reaction_type_statistics,
    source_dataset_statistics,
    temperature_statistics,
    yield_statistics,
)


def print_example(title: str, payload: dict) -> None:
    print(f"\n{title}")
    print("=" * len(title))
    print(json.dumps(payload, indent=2, default=str)[:4000])


def main() -> int:
    print_example("dataset_summary()", dataset_summary())
    print_example(
        'catalyst_statistics(reaction_type="Buchwald-Hartwig", limit=3)',
        catalyst_statistics(reaction_type="Buchwald-Hartwig", limit=3),
    )
    print_example(
        'yield_statistics(reaction_type="Suzuki")',
        yield_statistics(reaction_type="Suzuki"),
    )
    print_example(
        'yield_statistics(reaction_type="Buchwald-Hartwig")',
        yield_statistics(reaction_type="Buchwald-Hartwig"),
    )
    print_example(
        'temperature_statistics(reaction_type="Buchwald-Hartwig")',
        temperature_statistics(reaction_type="Buchwald-Hartwig"),
    )
    print_example("source_dataset_statistics(limit=3)", source_dataset_statistics(limit=3))
    print_example("reaction_type_statistics(limit=3)", reaction_type_statistics(limit=3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
