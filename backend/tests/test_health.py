"""День 2. Первый тест каркаса: сервис поднимается и отвечает."""


def test_health_returns_200(bare_client):
    r = bare_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert r.headers["X-Request-ID"]
