import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Product


FIXTURE_PRODUCTS = [
    Product(
        id=1,
        title="Mechanical Keyboard",
        description="Clicky RGB switches, budget mechanical keyboard",
        category="Gaming Keyboards",
        price=3999,
    ),
    Product(
        id=2,
        title="Premium Mechanical Keyboard",
        description="Hot-swappable mechanical keyboard",
        category="Gaming Keyboards",
        price=8999,
    ),
    Product(
        id=3,
        title="PSN Wallet Top-up",
        description="PlayStation Store credit, digital gift card",
        category="Gift Cards",
        price=2000,
    ),
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.load_products", lambda: FIXTURE_PRODUCTS)
    monkeypatch.setattr("app.main.init_embedding_index", lambda products: None)
    monkeypatch.setattr("app.main.semantic_search", lambda query, top_k: [])
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_soft_penalizes_over_budget_results(client):
    response = client.get("/search", params={"q": "mechanical keyboard under 5000"})
    assert response.status_code == 200

    body = response.json()
    assert body["applied_filters"]["price_max"] == 5000.0

    result_ids = [result["product"]["id"] for result in body["results"]]
    assert result_ids.index(1) < result_ids.index(2)

    over_budget = next(
        result for result in body["results"] if result["product"]["id"] == 2
    )
    assert over_budget["explanation"].get("price_penalty_applied") is True


def test_search_paginates_results(client):
    response = client.get(
        "/search", params={"q": "keyboard", "page": 1, "page_size": 1}
    )
    body = response.json()
    assert len(body["results"]) == 1
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["total_results"] >= 1
