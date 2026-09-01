import pytest

from app import catalog_store
from app.models import Product
from app.search.filters import apply_filters, extract_filters


@pytest.fixture(autouse=True)
def _set_catalog():
    catalog_store.set_current_products(
        [
            Product(
                id=1,
                title="Mechanical Keyboard",
                description="Clicky RGB keyboard",
                category="Gaming Keyboards",
                price=3999,
            ),
            Product(
                id=2,
                title="Ergonomic Chair",
                description="Reclining gaming chair",
                category="Gaming Chairs",
                price=12999,
            ),
            Product(
                id=3,
                title="PSN Wallet Top-up",
                description="PlayStation Store credit",
                category="Gift Cards",
                price=2000,
            ),
        ]
    )
    yield
    catalog_store.set_current_products([])


def test_extract_filters_parses_price_ceiling():
    filters = extract_filters("gaming keyboard under ₹5000")
    assert filters["price_max"] == 5000.0


def test_extract_filters_parses_price_with_commas_and_below():
    filters = extract_filters("below Rs. 12,999")
    assert filters["price_max"] == 12999.0


def test_extract_filters_finds_category_hint_ignoring_gaming_stopword():
    filters = extract_filters("budget gaming chairs")
    assert filters["category_hint"] == "Gaming Chairs"


def test_extract_filters_finds_category_hint_for_gift_cards():
    filters = extract_filters("gift cards for playstation")
    assert filters["category_hint"] == "Gift Cards"


def test_extract_filters_no_category_hint_for_brand_only_query():
    filters = extract_filters("playstation store credit")
    assert filters.get("category_hint") is None


def test_extract_filters_returns_empty_dict_for_unrelated_query():
    filters = extract_filters("dishwasher")
    assert filters == {}


def test_apply_filters_soft_penalizes_price_over_ceiling_and_resorts():
    results = [
        {"product": Product(id=1, title="A", description="", category="Gaming Keyboards", price=3999), "fused_score": 0.5, "explanation": {}},
        {"product": Product(id=2, title="B", description="", category="Gaming Keyboards", price=8999), "fused_score": 0.6, "explanation": {}},
    ]

    filtered = apply_filters(results, {"price_max": 5000.0})

    assert [r["product"].id for r in filtered] == [1, 2]
    assert filtered[1]["fused_score"] == pytest.approx(0.6 * 0.15)
    assert filtered[1]["explanation"]["price_penalty_applied"] is True
    assert "price_penalty_applied" not in filtered[0]["explanation"]


def test_apply_filters_soft_penalizes_category_mismatch_and_resorts():
    results = [
        {"product": Product(id=1, title="A", description="", category="Gaming Mice", price=1000), "fused_score": 0.5, "explanation": {}},
        {"product": Product(id=2, title="B", description="", category="Gaming Chairs", price=1000), "fused_score": 0.4, "explanation": {}},
    ]

    filtered = apply_filters(results, {"category_hint": "Gaming Chairs"})

    assert [r["product"].id for r in filtered] == [2, 1]
    assert filtered[1]["fused_score"] == pytest.approx(0.5 * 0.15)
    assert filtered[1]["explanation"]["category_penalty_applied"] is True


def test_apply_filters_stacks_penalties_when_both_filters_violated():
    results = [
        {"product": Product(id=1, title="A", description="", category="Gift Cards", price=8999), "fused_score": 1.0, "explanation": {}},
    ]

    filtered = apply_filters(results, {"price_max": 5000.0, "category_hint": "Gaming Chairs"})

    assert filtered[0]["fused_score"] == pytest.approx(1.0 * 0.15 * 0.15)
    assert filtered[0]["explanation"]["price_penalty_applied"] is True
    assert filtered[0]["explanation"]["category_penalty_applied"] is True


def test_apply_filters_passthrough_when_no_filters():
    results = [
        {"product": Product(id=1, title="A", description="", category="Gaming Mice", price=1000), "fused_score": 0.5, "explanation": {}},
    ]

    filtered = apply_filters(results, {})

    assert filtered == results
