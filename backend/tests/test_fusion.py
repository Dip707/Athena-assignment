import pytest

from app import catalog_store
from app.models import Product
from app.search.fusion import fuse_rankings


@pytest.fixture(autouse=True)
def _set_catalog():
    catalog_store.set_current_products(
        [
            Product(id=1, title="Mechanical Keyboard", description="Clicky RGB keyboard", category="Gaming Keyboards", price=3999),
            Product(id=2, title="Wireless Mouse", description="Ergonomic mouse", category="Gaming Mice", price=1499),
            Product(id=3, title="PlayStation Gift Card", description="PSN wallet top-up", category="Gift Cards", price=2000),
        ]
    )
    yield
    catalog_store.set_current_products([])


def test_fuse_rankings_combines_both_lists_in_expected_order():
    bm25_results = [(1, 1, 5.0), (2, 2, 3.0)]
    semantic_results = [(1, 1, 0.9), (2, 3, 0.5)]

    fused = fuse_rankings(bm25_results, semantic_results, alpha=1.0, beta=1.0, k=60)

    assert [r["product"].id for r in fused] == [1, 2]
    assert fused[0]["fused_score"] == pytest.approx(1 / 61 + 1 / 61)
    assert fused[1]["fused_score"] == pytest.approx(1 / 62 + 1 / 63)


def test_fuse_rankings_handles_product_missing_from_one_list():
    fused = fuse_rankings([(3, 1, 4.0)], [])

    assert len(fused) == 1
    result = fused[0]
    assert result["product"].id == 3
    assert result["semantic_rank"] is None
    assert result["fused_score"] == pytest.approx(1 / 61)
    assert result["explanation"]["semantic_contribution"] == 0.0


def test_fuse_rankings_ignores_ids_not_in_current_catalog():
    fused = fuse_rankings([(999, 1, 1.0)], [])
    assert fused == []


def test_fuse_rankings_breaks_equal_score_ties_by_product_id():
    fused = fuse_rankings([(2, 1, 1.0), (1, 1, 1.0)], [])
    assert [result["product"].id for result in fused] == [1, 2]
