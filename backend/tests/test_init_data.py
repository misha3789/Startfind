"""День 7. validate_init_data: 5 обязательных наборов initData + граничные случаи (ИС-01, ИС-02)."""
import time

import pytest

from app.errors import AuthError
from app.security import validate_init_data
from tests.helpers import BOT_TOKEN, make_init_data

NOW = 1_800_000_000


def check(init_data, **kw):
    return validate_init_data(init_data, BOT_TOKEN, now=NOW, **kw)


def assert_rejected(init_data, **kw):
    with pytest.raises(AuthError) as e:
        check(init_data, **kw)
    assert e.value.code == "AUTH_INVALID_INIT_DATA" and e.value.http == 401


# ---- 5 обязательных наборов ------------------------------------------------------
def test_1_valid_init_data_accepted():
    tg = check(make_init_data({"id": 42, "first_name": "Миша", "username": "misha"}, auth_date=NOW - 60))
    assert (tg.id, tg.first_name, tg.username) == (42, "Миша", "misha")


def test_2_tampered_signature_rejected():
    data = make_init_data(auth_date=NOW - 60)
    assert_rejected(data[:-1] + ("0" if data[-1] != "0" else "1"))


def test_3_expired_rejected():
    assert_rejected(make_init_data(auth_date=NOW - 86400 - 1))


def test_4_empty_rejected():
    assert_rejected("")


def test_5_without_user_field_rejected():
    # подпись верна, но поля user нет — личность пользователя неизвестна
    assert_rejected(make_init_data(with_user=False, auth_date=NOW - 60))


# ---- граничные значения и дополнительные случаи ----------------------------------
def test_age_boundary_exactly_max_age_is_valid():
    check(make_init_data(auth_date=NOW - 86400))          # ровно 24 ч — ещё действует


def test_future_auth_date_rejected():
    assert_rejected(make_init_data(auth_date=NOW + 3600))


def test_signed_with_another_bot_token_rejected():
    assert_rejected(make_init_data(auth_date=NOW - 60, bot_token="999:OTHER"))


def test_added_field_after_signing_rejected():
    assert_rejected(make_init_data(auth_date=NOW - 60) + "&admin=1")


def test_missing_hash_rejected():
    assert_rejected("auth_date=%d&user=%%7B%%22id%%22%%3A1%%7D" % (NOW - 60))


def test_user_is_not_json_rejected():
    assert_rejected(make_init_data(auth_date=NOW - 60, with_user=False, extra={"user": "not-json"}))


def test_garbage_rejected():
    assert_rejected("это вообще не initData")


def test_empty_bot_token_rejects_everything():
    with pytest.raises(AuthError):
        validate_init_data(make_init_data(auth_date=NOW - 60), "", now=NOW)


def test_custom_max_age_respected():
    assert_rejected(make_init_data(auth_date=NOW - 120), max_age=60)


def test_realtime_clock_works_without_now():
    tg = validate_init_data(make_init_data({"id": 5, "first_name": "A"}), BOT_TOKEN)
    assert tg.id == 5 and abs(tg.auth_date - time.time()) < 5


def test_is_02_missing_name_and_avatar_is_not_an_error():           # ИС-02
    tg = check(make_init_data({"id": 7}, auth_date=NOW - 60))
    assert tg.id == 7 and tg.first_name is None and tg.photo_url is None
