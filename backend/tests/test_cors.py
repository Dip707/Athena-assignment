from fastapi.testclient import TestClient

from app.main import app


def test_preflight_allows_localhost_and_loopback_frontends(monkeypatch):
    monkeypatch.setattr("app.main.init_embedding_index", lambda products: None)

    with TestClient(app) as client:
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            response = client.options(
                "/search",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                },
            )

            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
