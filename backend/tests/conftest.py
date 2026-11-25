import os

import pytest
from fastapi.testclient import TestClient

from tests.helpers import BOT_TOKEN

# Токен всегда тестовый: настоящий токен из окружения или пустой BOT_TOKEN из .env.example сломали бы тесты.
os.environ["BOT_TOKEN"] = BOT_TOKEN

# Модули приложения (app.db, app.main, app.models, app.access) импортируются внутри фикстур,
# поэтому тесты, которым приложение не нужно (test_init_data.py, часть test_errors.py),
# запускаются и до того, как архитектор вольёт каркас backend.


@pytest.fixture()
def engine(tmp_path):
    """Чистая БД на каждый тест. По умолчанию SQLite-файл; для PostgreSQL: TEST_DATABASE_URL=…"""
    from app.db import make_engine
    from app.models import Base
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path/'test.db'}"
    eng = make_engine(url)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    from app.db import make_session_factory
    s = make_session_factory(engine)()
    yield s
    s.close()


def _settings(database_url):
    from app.config import Settings
    return Settings(bot_token=BOT_TOKEN, database_url=database_url)


def _add_error_probes(application):
    """Маршруты-пробы единого формата ошибок: не требуют БД."""
    from app.errors import AppError

    @application.get("/probe/raise/{code}")
    def raise_code(code: str):
        raise AppError(code)

    @application.get("/probe/crash")
    def crash():
        raise RuntimeError("secret-internal-detail: password=hunter2")


@pytest.fixture()
def bare_app():
    """Приложение без БД: проверяет каркас, /health и обработчики ошибок."""
    from app.main import create_app
    application = create_app(_settings("sqlite://"))
    _add_error_probes(application)
    return application


@pytest.fixture()
def bare_client(bare_app):
    return TestClient(bare_app, raise_server_exceptions=False)


@pytest.fixture()
def app(engine, tmp_path):
    from fastapi import Depends
    from sqlalchemy.orm import Session

    from app.access import current_user, get_session, require_owner, require_role
    from app.main import create_app
    from app.models import User

    application = create_app(_settings(engine.url.render_as_string(hide_password=False)))
    _add_error_probes(application)

    # служебные маршруты-пробы: проверяют три рубежа доступа до появления настоящих эндпоинтов
    @application.get("/probe/founder-only")
    def founder_only(user: User = Depends(require_role("founder"))):
        return {"ok": True}

    @application.get("/probe/specialist-only")
    def specialist_only(user: User = Depends(require_role("specialist"))):
        return {"ok": True}

    @application.get("/probe/users/{owner_id}")
    def owned(owner_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
        require_owner(owner_id, user)
        owner = session.get(User, owner_id)
        return {"id": owner.id, "name": owner.name}

    return application


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def login(client):
    """login(user_id, name) -> заголовок авторизации; первый запрос создаёт пользователя."""
    from tests.helpers import auth_header
    def _login(tg_id=1001, name="Миша", username=None):
        user = {"id": tg_id, "first_name": name}
        if username:
            user["username"] = username
        headers = auth_header(user)
        assert client.post("/auth/telegram", headers=headers).status_code == 200
        return headers
    return _login
