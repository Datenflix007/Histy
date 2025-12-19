from __future__ import annotations


def test_api_health(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_search(client) -> None:
    response = client.post("/api/sources/search", json={"q": "Historia", "limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert payload["items"][0]["title"] == "Historia Regni"
