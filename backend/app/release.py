"""Build-time asset verification and an immutable public release receipt."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

RELEASE_PATH = Path(__file__).resolve().parents[1] / "release.json"
Sha = Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class ReleaseInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    revision: Sha | None = None
    index_sha256: Digest | None = None


def load_release(path: Path = RELEASE_PATH) -> ReleaseInfo:
    try:
        return ReleaseInfo.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ReleaseInfo()


def verify_release(revision: str, path: Path = RELEASE_PATH) -> ReleaseInfo:
    """Fail the build on stale corpus/model assets; never regenerate evidence."""
    validated = ReleaseInfo(revision=revision)
    from app.retrieval.artifacts import file_sha256
    from app.retrieval.dense import DEFAULT_EMBEDDINGS_PATH, DenseIndex
    from app.retrieval.loader import FactLoader

    chunks = FactLoader().load_all(include_private=False, include_unindexed=False)
    index = DenseIndex(chunks)
    # A real local query checks the cached model against the committed manifest too.
    if not index.search("engineering experience", top_k=1):
        raise ValueError("Release index contains no searchable public facts")
    info = validated.model_copy(
        update={"index_sha256": file_sha256(DEFAULT_EMBEDDINGS_PATH)}
    )
    temporary = path.with_suffix(".tmp")
    temporary.write_text(info.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default=os.environ.get("RENDER_GIT_COMMIT"))
    args = parser.parse_args()
    if not args.revision:
        parser.error("Provide --revision or RENDER_GIT_COMMIT; never infer a live SHA")
    print(json.dumps(verify_release(args.revision).model_dump()))


if __name__ == "__main__":
    main()
