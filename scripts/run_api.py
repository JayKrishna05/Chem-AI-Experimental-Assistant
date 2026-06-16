"""Run the local FastAPI backend."""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
