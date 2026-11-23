"""Единый формат ошибок Startfind: справочник из 27 кодов и иерархия исключений.

Источник: документ «Обработка исключительных ситуаций» (раздел 3 — типы,
приложение «Справочник кодов ошибок»). Формат ответа (раздел 2.2):
    {"code": ..., "message": ..., "fields": [...], "request_id": ...}
Доменный код выбрасывает конкретное исключение, единый обработчик превращает
его в HTTP-ответ по базовому классу — новая ситуация добавляется без правки
обработчика.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

logger = logging.getLogger("startfind")


@dataclass(frozen=True)
class ErrorSpec:
    code: str
    http: int | None  # None — «фон»: пользователю HTTP-ответа нет
    message: str
    situations: str


def _s(code, http, message, situations):
    return ErrorSpec(code, http, message, situations)


# ---- справочник кодов (27) --------------------------------------------------
CATALOG: dict[str, ErrorSpec] = {s.code: s for s in [
    _s("AUTH_INVALID_INIT_DATA", 401, "Сессия устарела. Откройте Startfind заново из Telegram.", "ИС-01"),
    _s("ACCESS_NOT_OWNER", 403, "Это действие доступно только автору проекта.", "ИС-13, 34"),
    _s("ACCESS_ROLE_REQUIRED", 403, "Это действие доступно другой роли. Добавить её в профиль?", "ИС-06"),
    _s("VAL_APPLICATION", 422, "Напишите, чем вам интересен проект (до 500 символов), и подтвердите часы.", "ИС-28"),
    _s("VAL_FILTER", 422, "Проверьте параметры фильтра.", "ИС-19"),
    _s("VAL_OUT_OF_RANGE", 422, "Укажите от 1 до 40 часов в неделю и ссылку вида https://…", "ИС-10"),
    _s("VAL_PROJECT_INCOMPLETE", 422, "Чтобы опубликовать проект, добавьте идею, стадию и хотя бы одну роль.", "ИС-11"),
    _s("VAL_REJECTION_REASON", 422, "Выберите причину отказа — кандидат увидит корректное сообщение.", "ИС-33"),
    _s("VAL_REQUIRED_FIELDS", 422, "Заполните направление, навыки и часы в неделю.", "ИС-07"),
    _s("VAL_ROLE_WITHOUT_SKILLS", 422, "Укажите хотя бы один навык для роли.", "ИС-12"),
    _s("VAL_SKILL_NOT_IN_CATALOG", 422, "Такого навыка нет в справочнике — выберите из списка.", "ИС-08"),
    _s("RULE_ALREADY_MEMBER", 409, "Специалист уже в команде на этой роли.", "ИС-30, 42"),
    _s("RULE_DUPLICATE_APPLICATION", 409, "Вы уже откликнулись на эту роль. Статус: …", "ИС-27"),
    _s("RULE_INVALID_STATUS_TRANSITION", 409, "Отклик уже в статусе «…», это действие недоступно.", "ИС-35"),
    _s("RULE_PROFILE_REQUIRED", 409, "Сначала заполните профиль — он приложится к отклику автоматически.", "ИС-29"),
    _s("RULE_PROJECT_NOT_ACTIVE", 409, "Проект сейчас не набирает участников.", "ИС-16"),
    _s("RULE_ROLE_CLOSED", 409, "Набор на эту роль закрыт. Посмотрите другие роли проекта.", "ИС-31, 32"),
    _s("RULE_ROLE_HAS_MEMBERS", 409, "В этой роли есть участники — сначала завершите их участие.", "ИС-14"),
    _s("RULE_SELF_APPLICATION", 409, "Нельзя откликнуться на роль в своём проекте.", "ИС-30"),
    _s("NF_PROJECT", 404, "Проект больше недоступен.", "ИС-17"),
    _s("EXT_BOT_BLOCKED", None, "Включите бота Startfind, чтобы получать уведомления.", "ИС-39"),
    _s("EXT_EMBEDDING_UNAVAILABLE", 200, "Не показывается — работает резервный подбор.", "ИС-23"),
    _s("EXT_TELEGRAM_UNAVAILABLE", None, "Не показывается — уведомление будет отправлено повторно.", "ИС-38"),
    _s("SYS_CONCURRENT_UPDATE", 409, "Отклик уже обработан — показываем актуальный статус.", "ИС-36"),
    _s("SYS_DB_UNAVAILABLE", 503, "Сервис временно недоступен. Попробуйте через минуту.", "ИС-45"),
    _s("SYS_INTERNAL", 500, "Что-то пошло не так.", "ИС-46"),
    _s("SYS_TRANSACTION_FAILED", 503, "Не удалось сохранить решение. Попробуйте ещё раз.", "ИС-37"),
]}
assert len(CATALOG) == 27

TYPE_PREFIXES = ("AUTH", "ACCESS", "VAL", "RULE", "NF", "EXT", "SYS")


# ---- иерархия исключений ----------------------------------------------------
class AppError(Exception):
    """Базовый класс. Конкретный код берётся из справочника."""

    default_code = "SYS_INTERNAL"

    def __init__(self, code: str | None = None, *, message: str | None = None,
                 fields: list[dict] | None = None):
        self.code = code or self.default_code
        if self.code not in CATALOG:
            raise ValueError(f"код {self.code!r} отсутствует в справочнике")
        spec = CATALOG[self.code]
        self.http = spec.http if spec.http is not None else 200
        self.message = message or spec.message
        self.fields = fields or []
        super().__init__(self.code)


class AuthError(AppError):               # 401
    default_code = "AUTH_INVALID_INIT_DATA"


class AccessError(AppError):             # 403
    default_code = "ACCESS_NOT_OWNER"


class ValidationAppError(AppError):      # 422
    default_code = "VAL_REQUIRED_FIELDS"


class RuleError(AppError):               # 409
    default_code = "RULE_INVALID_STATUS_TRANSITION"


class NotFoundError(AppError):           # 404
    default_code = "NF_PROJECT"


class ExternalError(AppError):           # фон / 200
    default_code = "EXT_TELEGRAM_UNAVAILABLE"


class SystemAppError(AppError):          # 409 / 500 / 503
    default_code = "SYS_INTERNAL"


# ---- ответ ------------------------------------------------------------------
def new_request_id() -> str:
    return uuid.uuid4().hex[:8]


def error_body(code: str, request_id: str, *, message: str | None = None,
               fields: list[dict] | None = None) -> dict:
    spec = CATALOG[code]
    body = {"code": code, "message": message or spec.message, "request_id": request_id}
    if fields:
        body["fields"] = fields
    return body


def install_handlers(app) -> None:
    """Подключает глобальные обработчики к приложению FastAPI."""
    from fastapi import Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    def rid(request: Request) -> str:
        return getattr(request.state, "request_id", None) or new_request_id()

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or new_request_id()
        try:
            response = await call_next(request)
        except Exception:  # непредвиденная ошибка → SYS_INTERNAL без стека для клиента
            logger.exception("unhandled error request_id=%s path=%s", request.state.request_id, request.url.path)
            return JSONResponse(error_body("SYS_INTERNAL", request.state.request_id,
                                           message=f"{CATALOG['SYS_INTERNAL'].message} Номер запроса: {request.state.request_id}"),
                                status_code=500)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(error_body(exc.code, rid(request), message=exc.message, fields=exc.fields),
                            status_code=exc.http)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(request: Request, exc: RequestValidationError):
        fields = [{"field": ".".join(str(p) for p in e["loc"] if p != "body") or "body", "issue": e["type"]}
                  for e in exc.errors()]
        return JSONResponse(error_body("VAL_REQUIRED_FIELDS", rid(request), fields=fields), status_code=422)
