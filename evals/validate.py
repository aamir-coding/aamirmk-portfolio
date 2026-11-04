"""Structural validation only: python -m evals.validate (no answer generation)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from evals.dataset import freeze_dataset, verify_dataset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Create the initial manifest; refuses overwrite",
    )
    parser.add_argument(
        "--include-held-out",
        action="store_true",
        help="Validate reserved case structure only; never score answers",
    )
    args = parser.parse_args()
    if args.freeze:
        freeze_dataset()
    print(json.dumps(verify_dataset(include_held_out=args.include_held_out), indent=2))


if __name__ == "__main__":
    main()
