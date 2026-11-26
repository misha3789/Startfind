"""Regression test for defect D-05."""


def test_unknown_route_uses_unified_error_format(bare_client):
    response = bare_client.get("/route-that-does-not-exist")
    body = response.json()
    assert response.status_code == 404
    assert body["code"] == "NF_PROJECT"
    assert set(body) >= {"code", "message", "request_id"}
