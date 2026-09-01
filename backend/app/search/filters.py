"""Filter extraction and soft-penalty application for search queries.

Natural-language queries may embed hard filters, e.g. "gaming keyboard
under ₹5000" -> price ceiling of 5000, or "PlayStation" -> a
category/brand hint. Price-ceiling extraction is mechanical (basic regex
matching), so it's implemented below as a reasonable starting point.
Category hints are extracted alongside price ceilings, then applied as soft
penalties so non-matching products remain available as fallback results.
"""

from __future__ import annotations

import re
from functools import lru_cache

from app.catalog_store import get_known_categories
from app.search.bm25 import tokenize

# Matches: "under 5000", "under ₹5000", "below Rs 5000", "under rs. 5,000", etc.
_PRICE_MAX_RE = re.compile(
    r"(?:under|below|less than)\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)

# Appears in nearly every category name in the sample dataset ("Gaming
# Keyboards", "Gaming Mice", "Gaming Chairs", ...) and carries no
# discriminating signal on its own.
_CATEGORY_STOPWORDS = {"gaming"}
_FILTER_MISMATCH_PENALTY = 0.15


def _normalize(token: str) -> str:
    """Naive singular/plural folding for category matching."""
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


@lru_cache(maxsize=512)
def _significant_tokens(text: str) -> frozenset[str]:
    """Tokenize a query/category once; category strings repeat across requests."""
    return frozenset(_normalize(t) for t in tokenize(text) if t not in _CATEGORY_STOPWORDS)


def extract_filters(query: str) -> dict:
    """Extract price and category hints embedded in a natural-language query."""
    filters: dict = {}

    match = _PRICE_MAX_RE.search(query)
    if match:
        raw_value = match.group(1).replace(",", "")
        filters["price_max"] = float(raw_value)

    query_tokens = _significant_tokens(query)
    best_category = None
    best_overlap = 0
    for category in sorted(get_known_categories()):
        overlap = len(query_tokens & _significant_tokens(category))
        if overlap > best_overlap:
            best_overlap = overlap
            best_category = category

    if best_category is not None:
        filters["category_hint"] = best_category

    return filters


def apply_filters(results: list[dict], filters: dict) -> list[dict]:
    """Apply soft penalties to fused search results.

    A violation of either ``price_max`` or ``category_hint`` multiplies the
    result's score by 0.15. Violations stack multiplicatively, and no result
    is removed from the returned list.
    """
    price_max = filters.get("price_max")
    category_hint = filters.get("category_hint")

    for result in results:
        product = result["product"]

        if price_max is not None and product.price > price_max:
            result["fused_score"] *= _FILTER_MISMATCH_PENALTY
            result["explanation"]["price_penalty_applied"] = True

        if category_hint is not None and product.category != category_hint:
            result["fused_score"] *= _FILTER_MISMATCH_PENALTY
            result["explanation"]["category_penalty_applied"] = True

    results.sort(key=lambda result: result["fused_score"], reverse=True)
    return results
