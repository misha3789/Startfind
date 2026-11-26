"""MVP database engine and session infrastructure."""
from types import SimpleNamespace

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.config import Settings
from app.db import make_engine, make_session_factory
from app.main import create_app


def test_make_engine_connects_to_configured_database(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'engine.db'}")
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
    finally:
        engine.dispose()


def test_make_session_factory_is_bound_to_engine(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'session.db'}")
    session = make_session_factory(engine)()
    try:
        assert isinstance(session, Session)
        assert session.bind is engine
        assert session.autoflush is False
        assert session.expire_on_commit is False
    finally:
        session.close()
        engine.dispose()


def test_db_dependency_closes_session():
    class TrackingSession:
        closed = False

        def close(self):
            self.closed = True

    session = TrackingSession()
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(session_factory=lambda: session),
        ),
    )

    dependency = get_db_session(request)
    assert next(dependency) is session
    dependency.close()

    assert session.closed is True


def test_create_app_uses_database_url_from_settings(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    application = create_app(Settings(bot_token="test-token", database_url=database_url))
    try:
        assert application.state.engine.url.render_as_string(hide_password=False) == database_url
        assert application.state.session_factory.kw["bind"] is application.state.engine
    finally:
        application.state.engine.dispose()
