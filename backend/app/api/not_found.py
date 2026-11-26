"""Unified response for unknown API routes (defect D-05)."""
from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..errors import error_body, new_request_id


def install_not_found_handler(app) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            request_id = getattr(request.state, "request_id", None) or new_request_id()
            return JSONResponse(error_body("NF_PROJECT", request_id), status_code=404)
        return await http_exception_handler(request, exc)
