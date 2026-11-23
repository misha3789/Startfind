"""Вспомогательные функции тестов: генерация подписанных данных запуска Mini App."""
import json
import time
from urllib.parse import urlencode

from app.security import sign_init_data

BOT_TOKEN = "123456:TEST-TOKEN-NOT-A-REAL-ONE"


def make_init_data(user: dict | None = None, *, auth_date: int | None = None, bot_token: str = BOT_TOKEN,
                   with_user: bool = True, extra: dict | None = None) -> str:
    fields = {"auth_date": str(int(time.time()) if auth_date is None else auth_date), "query_id": "AAE-test"}
    if with_user:
        fields["user"] = json.dumps(user or {"id": 1001, "first_name": "Миша", "username": "misha"}, ensure_ascii=False)
    fields.update(extra or {})
    fields["hash"] = sign_init_data(fields, bot_token)
    return urlencode(fields)


def auth_header(user: dict | None = None, **kw) -> dict:
    return {"Authorization": "tma " + make_init_data(user, **kw)}
