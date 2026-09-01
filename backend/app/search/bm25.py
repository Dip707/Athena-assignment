"""Lexical (BM25) search over the product catalog.

Builds a BM25Okapi index in-process (via the `rank_bm25` package) over
tokenized product text (title + " " + description). This is intentionally
kept separate from Qdrant — BM25 here is pure Python/NumPy, not Qdrant's
sparse vector support — to keep the lexical and semantic paths independent
and easy to reason about.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from app.data_loader import product_text
from app.models import Product

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase + alphanumeric tokenization used for BM25 indexing/queries."""
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    """Wraps a BM25Okapi index over a fixed product catalog.

    Instantiate once at startup with the full product list; `product_ids`
    preserves the mapping from BM25's internal (0-indexed) corpus position
    back to the product's `id` field.
    """

    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self.product_ids: list[int] = [p.id for p in products]
        corpus = [tokenize(product_text(p)) for p in products]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, int, float]]:
        """Rank products against `query` using BM25.

        Returns:
            A list of (product_id, rank, score) tuples, rank is 1-indexed
            and sorted descending by score. Products with a zero BM25
            score are excluded (they share no tokens with the query).
        """
        if self._bm25 is None:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(
            (
                (self.product_ids[i], float(score))
                for i, score in enumerate(scores)
                if score > 0
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        return [
            (product_id, rank, score)
            for rank, (product_id, score) in enumerate(ranked[:top_k], start=1)
        ]


# Module-level singleton, populated at app startup via init_bm25_index().
_index: BM25Index | None = None


def init_bm25_index(products: list[Product]) -> BM25Index:
    """Build (or rebuild) the module-level BM25 index. Call once at startup."""
    global _index
    _index = BM25Index(products)
    return _index


def bm25_search(query: str, top_k: int = 10) -> list[tuple[int, int, float]]:
    """Search the module-level BM25 index.

    Raises:
        RuntimeError: If init_bm25_index() has not been called yet
            (e.g. app startup didn't run or the catalog wasn't loaded).
    """
    if _index is None:
        raise RuntimeError(
            "BM25 index not initialized. Call init_bm25_index(products) "
            "at app startup before searching."
        )
    return _index.search(query, top_k=top_k)
