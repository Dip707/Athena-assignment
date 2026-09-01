import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Product


FIXTURE_PRODUCTS = [
    Product(
        id=1,
        title="Mechanical Keyboard",
        description="Clicky RGB switches",
        category="Gaming Keyboards",
        price=3999,
    ),
    Product(
        id=2,
        title="Gaming Chair",
        description="Reclining chair",
        category="Gaming Chairs",
        price=9999,
    ),
]


CURATION_CALLS = []


@pytest.fixture
def client(monkeypatch):
    CURATION_CALLS.clear()
    monkeypatch.setattr("app.main.load_products", lambda: FIXTURE_PRODUCTS)
    monkeypatch.setattr(
        "app.main.bm25_search",
        lambda query, top_k: [(1, 1, 1.0), (2, 2, 0.5)],
    )
    monkeypatch.setattr("app.main.init_embedding_index", lambda products: None)
    monkeypatch.setattr("app.main.semantic_search", lambda query, top_k: [])

    def fake_curate(query, filters, results, top_n=10):
        CURATION_CALLS.append((query, filters, results, top_n))
        tagged = dict(results[0])
        tagged["tag"] = "Best match"
        return [tagged] + results[1:]

    monkeypatch.setattr("app.main.curate_results", fake_curate)
    with TestClient(app) as test_client:
        yield test_client


def test_search_includes_curated_tag_in_response(client):
    response = client.get("/search", params={"q": "keyboard"})
    body = response.json()
    assert body["results"][0]["tag"] == "Best match"


def test_search_without_curation_skips_curator_and_returns_deterministic_results(client):
    response = client.get("/search", params={"q": "keyboard", "curate": "false"})

    assert response.status_code == 200
    body = response.json()
    assert [result["product"]["id"] for result in body["results"]] == [1, 2]
    assert [result["tag"] for result in body["results"]] == [None, None]
    assert CURATION_CALLS == []


def test_search_with_explicit_curation_preserves_curated_tag_serialization(client):
    response = client.get("/search", params={"q": "keyboard", "curate": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["tag"] == "Best match"
    assert len(CURATION_CALLS) == 1
