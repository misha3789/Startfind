"""Дни 7–8. Вход и выбор роли: ИС-01…ИС-03 и ИС-05…ИС-06 через HTTP API."""
from sqlalchemy import func

from app.access import get_or_create_user
from app.models import User, UserRole
from app.security import TelegramUser
from tests.helpers import auth_header, make_init_data


def count(session, model):
    session.expire_all()
    return session.query(func.count()).select_from(model).scalar()


# ---- ИС-01 -----------------------------------------------------------------------
def test_is01_invalid_signature_gives_401(client, session):
    bad = make_init_data()[:-2] + "00"
    r = client.post("/auth/telegram", headers={"Authorization": "tma " + bad})
    assert r.status_code == 401 and r.json()["code"] == "AUTH_INVALID_INIT_DATA"
    assert count(session, User) == 0                       # сессия и пользователь не создаются


def test_is01_expired_gives_401(client):
    r = client.post("/auth/telegram", headers=auth_header(auth_date=1_000_000_000))
    assert r.status_code == 401 and r.json()["code"] == "AUTH_INVALID_INIT_DATA"


def test_is01_no_authorization_header_gives_401(client):
    r = client.post("/auth/telegram")
    assert r.status_code == 401 and r.json()["code"] == "AUTH_INVALID_INIT_DATA"


# ---- ИС-02 -----------------------------------------------------------------------
def test_is02_user_without_name_is_created(client):
    r = client.post("/auth/telegram", headers=auth_header({"id": 555}))
    assert r.status_code == 200 and r.json()["name"] == "Участник Startfind"


def test_is02_username_used_instead_of_missing_name(client):
    r = client.post("/auth/telegram", headers=auth_header({"id": 556, "username": "anon"}))
    assert r.json()["name"] == "anon"


# ---- ИС-03 -----------------------------------------------------------------------
def test_is03_first_login_creates_user(client, session):
    r = client.post("/auth/telegram", headers=auth_header({"id": 1001, "first_name": "Миша"}))
    assert r.status_code == 200 and r.json()["roles"] == []
    assert count(session, User) == 1


def test_is03_second_login_uses_same_record(client, session):      # критерий приёмки дня 7
    h = auth_header({"id": 1001, "first_name": "Миша"})
    a = client.post("/auth/telegram", headers=h).json()
    b = client.post("/auth/telegram", headers=h).json()
    assert a["id"] == b["id"] and count(session, User) == 1


def test_is03_race_two_first_logins_return_existing_record(session, monkeypatch):
    """Гонка: проверка «пользователя нет» устарела — вставка нарушит UNIQUE, запись перечитывается."""
    import app.access as access
    tg = TelegramUser(id=2002, first_name="Гонка", last_name=None, username=None, photo_url=None, auth_date=0)
    first = get_or_create_user(session, tg)
    calls = {"n": 0}
    real = access._find

    def stale_find(s, tid):                                      # первый поиск «не видит» уже созданную запись
        calls["n"] += 1
        return None if calls["n"] == 1 else real(s, tid)

    monkeypatch.setattr(access, "_find", stale_find)
    second = get_or_create_user(session, tg)
    assert second.id == first.id and count(session, User) == 1


# ---- ИС-05 / выбор роли ---------------------------------------------------------
def test_role_choice_specialist(client, login):
    h = login()
    r = client.post("/me/roles", json={"role": "specialist"}, headers=h)
    assert r.status_code == 200 and r.json()["roles"] == ["specialist"]


def test_is05_repeated_role_is_idempotent(client, login, session):
    h = login()
    client.post("/me/roles", json={"role": "founder"}, headers=h)
    r = client.post("/me/roles", json={"role": "founder"}, headers=h)
    assert r.status_code == 200 and r.json()["roles"] == ["founder"]
    assert count(session, UserRole) == 1


def test_second_role_added_without_new_account(client, login, session):   # FR-02
    h = login()
    client.post("/me/roles", json={"role": "specialist"}, headers=h)
    r = client.post("/me/roles", json={"role": "founder"}, headers=h)
    assert r.json()["roles"] == ["founder", "specialist"]
    assert count(session, User) == 1


def test_empty_role_choice_rejected_422(client, login):
    h = login()
    r = client.post("/me/roles", json={}, headers=h)
    assert r.status_code == 422 and r.json()["code"] == "VAL_REQUIRED_FIELDS"
    assert r.json()["fields"]


def test_invalid_role_rejected_422(client, login):
    h = login()
    for bad in ("boss", "", "SPECIALIST"):
        r = client.post("/me/roles", json={"role": bad}, headers=h)
        assert r.status_code == 422 and r.json()["code"] == "VAL_REQUIRED_FIELDS"


def test_user_cannot_grant_himself_admin(client, login):
    h = login()
    r = client.post("/me/roles", json={"role": "admin"}, headers=h)
    assert r.status_code == 422
    assert client.get("/me", headers=h).json()["roles"] == []


def test_get_me_returns_roles(client, login):
    h = login()
    client.post("/me/roles", json={"role": "founder"}, headers=h)
    assert client.get("/me", headers=h).json()["roles"] == ["founder"]


# ---- ИС-06 -----------------------------------------------------------------------
def test_is06_specialist_cannot_use_founder_action(client, login):
    h = login()
    client.post("/me/roles", json={"role": "specialist"}, headers=h)
    r = client.get("/probe/founder-only", headers=h)
    assert r.status_code == 403 and r.json()["code"] == "ACCESS_ROLE_REQUIRED"


def test_is06_after_adding_role_action_is_allowed(client, login):
    h = login()
    client.post("/me/roles", json={"role": "specialist"}, headers=h)
    assert client.get("/probe/founder-only", headers=h).status_code == 403
    client.post("/me/roles", json={"role": "founder"}, headers=h)
    assert client.get("/probe/founder-only", headers=h).status_code == 200


# ---- дополнительные проверки входа и ролей -------------------------------------------
def test_is02_name_is_first_and_last_name(client):
    r = client.post("/auth/telegram", headers=auth_header({"id": 700, "first_name": "Иван", "last_name": "Петров"}))
    assert r.json()["name"] == "Иван Петров"


def test_is02_blank_name_falls_back_to_username_then_default(client):
    r = client.post("/auth/telegram", headers=auth_header({"id": 701, "first_name": "  ", "username": "ivan"}))
    assert r.json()["name"] == "ivan"
    r = client.post("/auth/telegram", headers=auth_header({"id": 702, "first_name": "  "}))
    assert r.json()["name"] == "Участник Startfind"


def test_unauthenticated_request_with_invalid_body_gives_401_not_422(client):
    r = client.post("/me/roles", json={"role": "boss"})
    assert r.status_code == 401 and r.json()["code"] == "AUTH_INVALID_INIT_DATA"


def test_domain_layer_also_rejects_admin_role(session):
    import pytest

    from app.access import add_role
    from app.errors import ValidationAppError
    tg = TelegramUser(id=3003, first_name="Админ", last_name=None, username=None, photo_url=None, auth_date=0)
    user = get_or_create_user(session, tg)
    with pytest.raises(ValidationAppError):
        add_role(session, user.id, "admin")


def test_integration_login_then_role_then_me(client):
    """Сквозной сценарий этапа 2: вход → выбор роли → чтение профиля доступа."""
    headers = auth_header({"id": 777001, "first_name": "Анна"})
    r = client.post("/auth/telegram", headers=headers)
    assert r.status_code == 200 and r.json()["roles"] == []
    r = client.post("/me/roles", headers=headers, json={"role": "specialist"})
    assert r.status_code == 200
    r = client.get("/me", headers=headers)
    assert r.json()["name"] == "Анна" and r.json()["roles"] == ["specialist"]
