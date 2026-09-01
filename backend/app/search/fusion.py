"""Rank fusion — combines BM25 and semantic search results via weighted
Reciprocal Rank Fusion (RRF).

RRF fuses on rank position, not raw score, which is why BM25's unbounded
scores and cosine similarity's [-1,1] scores never need to be normalized
against each other here.
"""

from __future__ import annotations

from app.catalog_store import get_products_by_id


def fuse_rankings(
    bm25_results: list[tuple[int, int, float]],
    semantic_results: list[tuple[int, int, float]],
    alpha: float = 1.0,
    beta: float = 1.0,
    k: int = 60,
) -> list[dict]:
    """Combine BM25 and semantic rankings via weighted RRF.

    A product absent from one retriever contributes exactly zero for that
    retriever. IDs not present in the current catalog are discarded.
    """
    bm25_by_id = {pid: (rank, score) for pid, rank, score in bm25_results}
    semantic_by_id = {pid: (rank, score) for pid, rank, score in semantic_results}
    product_ids = set(bm25_by_id) | set(semantic_by_id)
    products_by_id = get_products_by_id()

    fused: list[dict] = []
    for product_id in product_ids:
        product = products_by_id.get(product_id)
        if product is None:
            continue

        bm25_rank, bm25_score = bm25_by_id.get(product_id, (None, None))
        semantic_rank, semantic_score = semantic_by_id.get(product_id, (None, None))
        bm25_contribution = alpha / (k + bm25_rank) if bm25_rank is not None else 0.0
        semantic_contribution = (
            beta / (k + semantic_rank) if semantic_rank is not None else 0.0
        )

        fused.append(
            {
                "product": product,
                "bm25_rank": bm25_rank,
                "semantic_rank": semantic_rank,
                "bm25_score": bm25_score,
                "semantic_score": semantic_score,
                "fused_score": bm25_contribution + semantic_contribution,
                "explanation": {
                    "bm25_contribution": round(bm25_contribution, 6),
                    "semantic_contribution": round(semantic_contribution, 6),
                },
            }
        )

    fused.sort(key=lambda result: (-result["fused_score"], result["product"].id))
    return fused
