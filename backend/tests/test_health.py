def test_health_returns_payload(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert data["database"] in ("connected", "degraded")


def test_health_db_returns_shape(client) -> None:
    r = client.get("/health/db")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data and "database" in data
    if r.status_code == 200:
        assert data == {"status": "ok", "database": "connected"}
    else:
        assert data == {"status": "error", "database": "disconnected"}
