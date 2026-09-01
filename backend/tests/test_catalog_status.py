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
        title="Desk Lamp",
        description="Adjustable reading light",
        category="Home",
        price=899,
    ),
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.load_products", lambda: FIXTURE_PRODUCTS)
    monkeypatch.setattr("app.main.init_embedding_index", lambda products: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with TestClient(app) as test_client:
        yield test_client


def test_catalog_status_reports_loaded_count_without_ai_key(client):
    response = client.get("/catalog/status")

    assert response.status_code == 200
    assert response.json() == {
        "loaded": True,
        "product_count": 2,
        "ai_enabled": False,
    }
    assert "GEMINI_API_KEY" not in response.text


def test_catalog_status_reports_empty_catalog_when_file_is_missing(monkeypatch):
    def missing_catalog():
        raise FileNotFoundError("catalog missing")

    monkeypatch.setattr("app.main.load_products", missing_catalog)
    monkeypatch.setattr("app.main.init_embedding_index", lambda products: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with TestClient(app) as client:
        response = client.get("/catalog/status")

    assert response.status_code == 200
    assert response.json() == {
        "loaded": False,
        "product_count": 0,
        "ai_enabled": False,
    }


def test_catalog_status_only_reports_that_ai_is_enabled(monkeypatch):
    monkeypatch.setattr("app.main.load_products", lambda: FIXTURE_PRODUCTS)
    monkeypatch.setattr("app.main.init_embedding_index", lambda products: None)
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")

    with TestClient(app) as client:
        response = client.get("/catalog/status")

    assert response.status_code == 200
    assert response.json()["ai_enabled"] is True
    assert "test-secret-key" not in response.text
