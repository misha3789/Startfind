"""День 10. Smoke-проверка стенда по сети.

Запуск:  STAND_URL=https://stand.example.ru pytest tests/smoke -q
Для проверки входа задайте SMOKE_INIT_DATA — реальные данные запуска Mini App
(скопировать из консоли браузера Telegram Desktop) либо подпишите их своим токеном
стенда скриптом scripts/make_init_data.py.
Без STAND_URL все проверки пропускаются, чтобы не ломать обычный прогон pytest.
"""
import os
import time

import pytest

httpx = pytest.importorskip("httpx")
STAND = os.environ.get("STAND_URL", "").rstrip("/")
pytestmark = [pytest.mark.smoke, pytest.mark.skipif(not STAND, reason="STAND_URL не задан")]


@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=STAND, timeout=10, follow_redirects=False) as c:
        yield c


def test_stand_uses_https():
    assert STAND.startswith("https://"), "Mini App в Telegram открывается только по HTTPS"


def test_health_ok_and_fast(http):
    t = time.perf_counter()
    r = http.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    assert time.perf_counter() - t < 2


def test_protected_endpoint_without_token_gives_401_in_unified_format(http):
    r = http.get("/me")
    assert r.status_code == 401 and r.json()["code"] == "AUTH_INVALID_INIT_DATA"
    assert "Traceback" not in r.text


def test_forged_init_data_rejected(http):
    r = http.get("/me", headers={"Authorization": "tma auth_date=1&hash=00"})
    assert r.status_code == 401


def test_http_redirects_or_closed():
    if STAND.startswith("https://"):
        plain = "http://" + STAND[len("https://"):]
        try:
            r = httpx.get(plain + "/health", timeout=5, follow_redirects=False)
        except httpx.HTTPError:
            return                                      # порт 80 закрыт — допустимо
        assert r.status_code in (301, 302, 307, 308), "по HTTP сервис не должен отвечать данными"


@pytest.mark.skipif(not os.environ.get("SMOKE_INIT_DATA"), reason="SMOKE_INIT_DATA не задан")
def test_login_works_and_is_idempotent(http):
    h = {"Authorization": "tma " + os.environ["SMOKE_INIT_DATA"]}
    a = http.post("/auth/telegram", headers=h)
    b = http.post("/auth/telegram", headers=h)
    assert a.status_code == 200 and b.status_code == 200 and a.json()["id"] == b.json()["id"]
