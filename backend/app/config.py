"""Настройки приложения из переменных окружения (список — в .env.example)."""
import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_INIT_DATA_MAX_AGE = 86400  # срок действия initData, секунды


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    init_data_max_age: int = DEFAULT_INIT_DATA_MAX_AGE


def get_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Читает настройки; при ошибке конфигурации падает сразу, без значений секретов в тексте."""
    env = os.environ if env is None else env
    bot_token = env.get("BOT_TOKEN", "").strip()
    database_url = env.get("DATABASE_URL", "").strip()
    missing = [name for name, value in (("BOT_TOKEN", bot_token), ("DATABASE_URL", database_url)) if not value]
    if missing:
        raise RuntimeError(f"Не заданы переменные окружения: {', '.join(missing)} (см. .env.example)")
    raw_age = env.get("INIT_DATA_MAX_AGE", "").strip() or str(DEFAULT_INIT_DATA_MAX_AGE)
    try:
        max_age = int(raw_age)
    except ValueError:
        max_age = 0
    if max_age <= 0:
        raise RuntimeError("INIT_DATA_MAX_AGE должен быть целым положительным числом секунд")
    return Settings(bot_token=bot_token, database_url=database_url, init_data_max_age=max_age)
