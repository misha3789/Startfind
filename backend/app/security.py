"""Проверка подписи данных запуска Telegram Mini App (initData).

Алгоритм Telegram (core.telegram.org/bots/webapps#validating-data-received-via-a-mini-app):
  secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
  hash       = HMAC_SHA256(key=secret_key, msg=data_check_string)
  data_check_string — пары key=value без поля hash, отсортированные по ключу, через \\n.
Дополнительно проверяется срок действия (auth_date) — ИС-01.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from .errors import AuthError

CLOCK_SKEW = 300  # допустимое расхождение часов, секунды


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    photo_url: str | None
    auth_date: int


def _invalid() -> AuthError:
    return AuthError("AUTH_INVALID_INIT_DATA")


def sign_init_data(fields: dict[str, str], bot_token: str) -> str:
    """Подписывает набор полей так же, как это делает Telegram (нужно тестам и smoke-скрипту)."""
    check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()


def validate_init_data(init_data: str, bot_token: str, *, max_age: int = 86400,
                       now: float | None = None) -> TelegramUser:
    """Возвращает пользователя Telegram или бросает AuthError(AUTH_INVALID_INIT_DATA)."""
    if not init_data or not bot_token:
        raise _invalid()
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        raise _invalid()
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise _invalid()
    expected = sign_init_data(pairs, bot_token)
    if not hmac.compare_digest(expected, received_hash):
        raise _invalid()

    now = time.time() if now is None else now
    try:
        auth_date = int(pairs["auth_date"])
    except (KeyError, ValueError):
        raise _invalid()
    if auth_date > now + CLOCK_SKEW or now - auth_date > max_age:
        raise _invalid()

    try:
        user = json.loads(pairs["user"])
        user_id = int(user["id"])
    except (KeyError, ValueError, TypeError):
        raise _invalid()
    return TelegramUser(
        id=user_id,
        first_name=user.get("first_name") or None,
        last_name=user.get("last_name") or None,
        username=user.get("username") or None,
        photo_url=user.get("photo_url") or None,
        auth_date=auth_date,
    )
