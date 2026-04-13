def test_health_returns_payload(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert data["database"] in ("connected", "degraded")
