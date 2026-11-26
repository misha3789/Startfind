"""Точка входа: фабрика приложения FastAPI."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.auth import router as auth_router
from .api.catalog import router as catalog_router
from .api.not_found import install_not_found_handler
from .api.profile import router as profile_router
from .config import Settings, get_settings
from .db import make_engine, make_session_factory
from .errors import install_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Startfind API", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    install_handlers(app)
    install_not_found_handler(app)
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(profile_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


def app_factory() -> FastAPI:
    """Для запуска: uvicorn app.main:app_factory --factory"""
    return create_app()
