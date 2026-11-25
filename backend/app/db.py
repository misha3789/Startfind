"""SQLAlchemy engine and session factory configuration."""
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str) -> Engine:
    """Create an engine for the configured database URL."""
    connect_args = {}
    if make_url(database_url).get_backend_name() == "sqlite":
        # FastAPI tests may use the same SQLite connection from another thread.
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    if make_url(database_url).get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create the application's SQLAlchemy Session factory."""
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
