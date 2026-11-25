"""Точка входа: фабрика приложения FastAPI."""
from fastapi import FastAPI

from .config import Settings, get_settings
from .errors import install_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Startfind API")
    app.state.settings = settings
    install_handlers(app)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


def app_factory() -> FastAPI:
    """Для запуска: uvicorn app.main:app_factory --factory"""
    return create_app()
