"""Okapi BM25 lexical keyword retrieval index.

Pure Python in-process implementation with technical tokenization and non-negative
Robertson-Spärck Jones IDF weighting.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from app.retrieval.models import FactChunk, RetrievedChunk

# Regex capturing technical tokens (C++, Node.js, 9.77, full-stack, alphanumeric)
_TOKEN_PATTERN = re.compile(
    r"[a-zA-Z0-9]+(?:\+\+)(?:17|20)?|"
    r"[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)+|"
    r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+|"
    r"[a-zA-Z0-9]+"
)


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase technical keywords, compounds, and sub-tokens."""
    if not text:
        return []

    raw_matches = _TOKEN_PATTERN.findall(text)
    tokens: list[str] = []

    for raw in raw_matches:
        t = raw.lower()
        tokens.append(t)

        # Emit sub-tokens for compound identifiers
        if "-" in t:
            tokens.extend([part for part in t.split("-") if part])
        elif "." in t:
            tokens.extend([part for part in t.split(".") if part])
        elif t.endswith("++17"):
            tokens.append(t[:-2])  # c++
            tokens.append("17")
        elif t.endswith("++20"):
            tokens.append(t[:-2])
            tokens.append("20")

    return tokens


class BM25Index:
    """In-memory Okapi BM25 index for keyword search over FactChunks."""

    def __init__(
        self,
        chunks: list[FactChunk] | None = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        """Initialize BM25 index with tuning parameters k1 and b."""
        self.k1 = k1
        self.b = b
        self.chunks: list[FactChunk] = []
        self._doc_lens: dict[str, int] = {}
        self._doc_tfs: dict[str, Counter[str]] = {}
        self._df: Counter[str] = Counter()
        self._avgdl: float = 0.0

        if chunks:
            self.index(chunks)

    def index(self, chunks: list[FactChunk]) -> None:
        """Build term frequency and document frequency indexes over the chunks."""
        self.chunks = list(chunks)
        self._doc_lens.clear()
        self._doc_tfs.clear()
        self._df.clear()

        if not self.chunks:
            self._avgdl = 0.0
            return

        total_tokens = 0
        for chunk in self.chunks:
            tag_str = " ".join(chunk.tags)
            doc_text = f"{chunk.title} {tag_str} {chunk.content}"
            tokens = tokenize(doc_text)
            token_count = len(tokens)

            self._doc_lens[chunk.id] = token_count
            self._doc_tfs[chunk.id] = Counter(tokens)
            total_tokens += token_count

            for term in set(tokens):
                self._df[term] += 1

        self._avgdl = total_tokens / len(self.chunks)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Search the index for a query and return top-k scored chunks.

        Uses Okapi BM25 formula with Robertson-Spärck Jones IDF:
            IDF(t) = ln( (N - n(t) + 0.5) / (n(t) + 0.5) + 1.0 )
        """
        if not self.chunks or top_k <= 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        n_docs = len(self.chunks)
        scores: list[tuple[float, FactChunk]] = []

        for chunk in self.chunks:
            cid = chunk.id
            dl = self._doc_lens[cid]
            tf = self._doc_tfs[cid]
            score = 0.0

            for term in query_tokens:
                if term not in tf:
                    continue

                n_t = self._df[term]
                # Log-odds Robertson-Spärck Jones IDF with +1 guarantee
                idf = math.log((n_docs - n_t + 0.5) / (n_t + 0.5) + 1.0)

                f = tf[term]
                # BM25 term frequency saturation
                denom = f + self.k1 * (1.0 - self.b + self.b * (dl / self._avgdl))
                tf_weight = (f * (self.k1 + 1.0)) / denom

                score += idf * tf_weight

            if score > 0.0:
                scores.append((score, chunk))

        scores.sort(key=lambda item: item[0], reverse=True)

        results: list[RetrievedChunk] = []
        for rank_idx, (score, chunk) in enumerate(scores[:top_k], start=1):
            results.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=round(score, 4),
                    rank=rank_idx,
                    retrieval_method="bm25",
                )
            )

        return results
