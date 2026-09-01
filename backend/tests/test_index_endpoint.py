import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.main.load_products", lambda: [])
    monkeypatch.setattr("app.main.init_embedding_index", lambda products: None)
    monkeypatch.setattr("app.main.semantic_search", lambda query, top_k: [])
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with TestClient(app) as test_client:
        yield test_client


def test_index_replaces_catalog_and_search_reflects_it(client):
    new_products = [
        {
            "id": 101,
            "title": "Retro Arcade Joystick",
            "description": "Classic arcade-style joystick controller",
            "category": "Gaming Controllers",
            "price": 2499,
        },
        {
            "id": 103,
            "title": "USB-C Charging Cable",
            "description": "Braided cable for charging devices",
            "category": "Accessories",
            "price": 499,
        },
        {
            "id": 105,
            "title": "Wireless Mouse",
            "description": "Ergonomic mouse for office and gaming",
            "category": "Accessories",
            "price": 1299,
        },
    ]

    index_response = client.post("/index", json=new_products)
    assert index_response.status_code == 200
    assert index_response.json() == {"indexed": 3}

    search_response = client.get("/search", params={"q": "arcade joystick"})
    result_ids = [r["product"]["id"] for r in search_response.json()["results"]]
    assert 101 in result_ids


def test_index_degrades_to_bm25_when_embedding_rebuild_fails(client, monkeypatch):
    def fail_embedding_rebuild(products):
        raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr("app.main.init_embedding_index", fail_embedding_rebuild)

    response = client.post(
        "/index",
        json=[
            {
                "id": 102,
                "title": "Studio Headphones",
                "description": "Closed-back monitoring headphones",
                "category": "Audio",
                "price": 1999,
            },
            {
                "id": 104,
                "title": "Desk Lamp",
                "description": "Adjustable reading light",
                "category": "Home",
                "price": 899,
            },
            {
                "id": 106,
                "title": "Notebook Stand",
                "description": "Aluminum stand for laptops",
                "category": "Home",
                "price": 1499,
            },
        ],
    )

    assert response.status_code == 200
    assert response.json() == {"indexed": 3}
    assert app.state.embeddings_ready is False

    search_response = client.get("/search", params={"q": "studio headphones"})
    assert search_response.status_code == 200
    assert search_response.json()["results"][0]["product"]["id"] == 102
