"""День 11. Проверки безопасности этапа 2: три рубежа — подлинность → роль → владение
(документ «Безопасность», раздел 3–4; тест-план, раздел 7)."""
import pytest

from tests.helpers import BOT_TOKEN, auth_header, make_init_data

PROTECTED = [("get", "/me"), ("post", "/auth/telegram"), ("get", "/probe/founder-only"),
             ("get", "/probe/specialist-only"), ("get", "/probe/users/1")]


def call(client, method, url, headers=None):
    return getattr(client, method)(url, headers=headers)


# ---- рубеж 1: подлинность ----------------------------------------------------------
@pytest.mark.parametrize("method, url", PROTECTED)
def test_no_token_gives_401(client, method, url):
    r = call(client, method, url)
    assert r.status_code == 401 and r.json()["code"] == "AUTH_INVALID_INIT_DATA"


@pytest.mark.parametrize("header", ["Bearer abc", "tma ", "tma garbage", "Basic Zm9vOmJhcg==", ""])
def test_malformed_authorization_gives_401(client, header):
    r = client.get("/me", headers={"Authorization": header})
    assert r.status_code == 401 and r.json()["code"] == "AUTH_INVALID_INIT_DATA"


def test_forged_signature_gives_401(client):
    data = make_init_data()
    forged = data[:-4] + ("abcd" if not data.endswith("abcd") else "dcba")
    assert client.get("/me", headers={"Authorization": "tma " + forged}).status_code == 401


def test_token_signed_with_other_bot_gives_401(client):
    r = client.get("/me", headers=auth_header(bot_token="1:ATTACKER"))
    assert r.status_code == 401


def test_impersonation_by_changing_user_id_after_signing_gives_401(client, login):
    """Злоумышленник меняет id пользователя в подписанных данных, не зная токена бота."""
    login(1001, "Жертва")
    data = make_init_data({"id": 1001, "first_name": "Жертва"})
    attacker = data.replace("1001", "9999")
    r = client.get("/me", headers={"Authorization": "tma " + attacker})
    assert r.status_code == 401


def test_expired_token_gives_401(client):
    r = client.get("/me", headers=auth_header(auth_date=1_000_000_000))
    assert r.status_code == 401


# ---- рубеж 2: роль -----------------------------------------------------------------
def test_action_without_role_gives_403(client, login):
    h = login()
    for url in ("/probe/founder-only", "/probe/specialist-only"):      # ни одной роли
        r = client.get(url, headers=h)
        assert r.status_code == 403 and r.json()["code"] == "ACCESS_ROLE_REQUIRED"


def test_role_does_not_grant_the_other_roles_rights(client, login):
    h = login()
    client.post("/me/roles", json={"role": "founder"}, headers=h)
    assert client.get("/probe/founder-only", headers=h).status_code == 200
    r = client.get("/probe/specialist-only", headers=h)
    assert r.status_code == 403 and r.json()["code"] == "ACCESS_ROLE_REQUIRED"


# ---- рубеж 3: владение объектом -----------------------------------------------------
def test_own_data_is_available(client, login):
    h = login(1001, "Алиса")
    me = client.get("/me", headers=h).json()
    r = client.get(f"/probe/users/{me['id']}", headers=h)
    assert r.status_code == 200 and r.json()["first_name"] == "Алиса"


def test_foreign_data_gives_403_without_leak(client, login):
    alice = login(1001, "Алиса", username="alice_secret")
    bob = login(2002, "Боб", username="bob_secret")
    alice_id = client.get("/me", headers=alice).json()["id"]
    r = client.get(f"/probe/users/{alice_id}", headers=bob)
    assert r.status_code == 403 and r.json()["code"] == "ACCESS_NOT_OWNER"
    for secret in ("Алиса", "alice_secret", "1001"):                    # текст ответа не раскрывает чужие данные
        assert secret not in r.text


def test_access_errors_do_not_reveal_whether_object_exists(client, login):
    alice = login(1001, "Алиса")
    bob = login(2002, "Боб")
    alice_id = client.get("/me", headers=alice).json()["id"]
    existing = client.get(f"/probe/users/{alice_id}", headers=bob).json()
    missing = client.get("/probe/users/987654", headers=bob).json()
    # чужой существующий и несуществующий объект неотличимы по коду и тексту
    assert (existing["code"], existing["message"]) == (missing["code"], missing["message"]) == (
        "ACCESS_NOT_OWNER", existing["message"])


# ---- секреты --------------------------------------------------------------------------
def test_bot_token_never_in_responses_or_logs(client, login, caplog):
    caplog.set_level("DEBUG")
    h = login()
    responses = [client.get("/probe/crash"), client.get("/me"), client.get("/probe/founder-only", headers=h),
                 client.get("/me", headers=auth_header(bot_token="1:ATTACKER"))]
    for r in responses:
        assert BOT_TOKEN not in r.text
    assert BOT_TOKEN not in caplog.text


def test_health_is_public_and_leaks_nothing(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
