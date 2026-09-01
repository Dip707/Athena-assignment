"""Pydantic schemas shared across the API layer.

These models define the request/response contract for the search API.
Fields related to the (still-undesigned) fusion/explanation logic are
intentionally left generous/optional so app/search/fusion.py can populate
them once the algorithm is finalized, without requiring another schema
migration.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Product(BaseModel):
    """A single product record, as loaded from data/products.json."""

    id: int
    title: str
    description: str
    category: str
    price: float


class SearchResult(BaseModel):
    """A single ranked result returned to the client.

    bm25_rank / semantic_rank are 1-indexed ranks within their respective
    result lists, or None if the product did not appear in that list at all.
    fused_score is the final combined score used for ordering.

    `explanation` is left open-ended (dict) so the fusion step can attach
    whatever per-component contribution breakdown it ends up needing
    (e.g. {"bm25_contribution": 0.01, "semantic_contribution": 0.02})
    without another schema change.
    """

    product: Product
    bm25_rank: Optional[int] = None
    semantic_rank: Optional[int] = None
    bm25_score: Optional[float] = None
    semantic_score: Optional[float] = None
    fused_score: Optional[float] = None
    tag: Optional[str] = Field(
        default=None,
        description="Set only on AI-curated slots, e.g. 'Outside your category'.",
    )
    explanation: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional per-component score breakdown for ranking explainability.",
    )


class SearchResponse(BaseModel):
    """Top-level response envelope for GET /search."""

    query: str
    results: list[SearchResult]
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    total_results: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
