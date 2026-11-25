"""День 2. Конфигурация: обязательные переменные, значения по умолчанию, секреты не попадают в текст ошибки."""
import pytest

from app.config import DEFAULT_INIT_DATA_MAX_AGE, get_settings

ENV = {"BOT_TOKEN": "123456:TEST-TOKEN-NOT-A-REAL-ONE", "DATABASE_URL": "postgresql+psycopg://u:p@localhost/db"}


def test_settings_are_read_with_default_max_age():
    s = get_settings(ENV)
    assert s.bot_token == ENV["BOT_TOKEN"] and s.database_url == ENV["DATABASE_URL"]
    assert s.init_data_max_age == DEFAULT_INIT_DATA_MAX_AGE


def test_max_age_can_be_overridden():
    assert get_settings({**ENV, "INIT_DATA_MAX_AGE": "3600"}).init_data_max_age == 3600


@pytest.mark.parametrize("missing", ["BOT_TOKEN", "DATABASE_URL"])
@pytest.mark.parametrize("empty", [False, True])
def test_required_variable_is_missing(missing, empty):
    env = {k: v for k, v in ENV.items() if k != missing}
    if empty:                                               # пустое значение из .env.example = не задано
        env[missing] = "  "
    with pytest.raises(RuntimeError, match=missing):
        get_settings(env)


@pytest.mark.parametrize("bad", ["abc", "0", "-5", "1.5"])
def test_invalid_max_age_is_rejected(bad):
    with pytest.raises(RuntimeError, match="INIT_DATA_MAX_AGE"):
        get_settings({**ENV, "INIT_DATA_MAX_AGE": bad})


def test_error_does_not_contain_secret_values():
    with pytest.raises(RuntimeError) as err:
        get_settings({"BOT_TOKEN": ENV["BOT_TOKEN"], "DATABASE_URL": ""})
    assert ENV["BOT_TOKEN"] not in str(err.value)
