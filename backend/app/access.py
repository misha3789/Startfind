"""Доступ в три рубежа (документ «Безопасность»): подлинность → роль → владение объектом.

1. current_user — проверяет подпись initData из заголовка `Authorization: tma <initData>`
   и возвращает пользователя (при первом входе создаёт запись, ИС-01…ИС-03).
2. require_role — роль пользователя (ИС-06).
3. require_owner — объект принадлежит пользователю (ИС-13, ИС-34).
"""
from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .api.dependencies import get_db_session as get_session
from .errors import AccessError, AuthError, ValidationAppError
from .models import User, UserRole
from .security import TelegramUser, validate_init_data

__all__ = ["get_session", "get_or_create_user", "get_roles", "add_role", "telegram_user", "current_user",
           "require_role", "require_owner", "ASSIGNABLE_ROLES", "DEFAULT_NAME"]

DEFAULT_NAME = "Участник Startfind"
ASSIGNABLE_ROLES = ("specialist", "founder")  # роль admin пользователь себе назначить не может


# ---- пользователь ---------------------------------------------------------------------
def display_name(tg: TelegramUser) -> str:
    """Имя из Telegram; если его нет — username, иначе «Участник Startfind» (ИС-02)."""
    full_name = " ".join(part.strip() for part in (tg.first_name, tg.last_name) if part and part.strip())
    return (full_name or (tg.username or "").strip() or DEFAULT_NAME)[:255]


def _find(session: Session, telegram_id: int) -> User | None:
    return session.scalar(select(User).where(User.telegram_id == telegram_id))


def get_or_create_user(session: Session, tg: TelegramUser) -> User:
    """Находит пользователя по telegram_id или создаёт и фиксирует (ИС-03).

    Если параллельный первый вход успел создать запись раньше, нарушится UNIQUE по telegram_id:
    тогда возвращается уже существующая запись, а не ошибка.
    """
    user = _find(session, tg.id)
    if user is not None:
        return user
    user = User(telegram_id=tg.id, name=display_name(tg))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = _find(session, tg.id)
        if existing is None:  # нарушено что-то другое, а не UNIQUE по telegram_id
            raise
        return existing
    return user


# ---- роли -----------------------------------------------------------------------------
def get_roles(session: Session, user_id: int) -> list[str]:
    return sorted(session.scalars(select(UserRole.role).where(UserRole.user_id == user_id)))


def add_role(session: Session, user_id: int, role: str) -> list[str]:
    """Добавляет роль, повторный выбор той же роли ничего не меняет (ИС-05, FR-02)."""
    if role not in ASSIGNABLE_ROLES:
        raise ValidationAppError(fields=[{"field": "role", "issue": "unsupported_role"}])
    if role not in get_roles(session, user_id):
        session.add(UserRole(user_id=user_id, role=role))
        try:
            session.commit()
        except IntegrityError:  # параллельный запрос уже добавил эту роль
            session.rollback()
    return get_roles(session, user_id)


# ---- рубеж 1: подлинность -------------------------------------------------------------
def telegram_user(request: Request) -> TelegramUser:
    scheme, _, init_data = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "tma" or not init_data.strip():
        raise AuthError("AUTH_INVALID_INIT_DATA")
    settings = request.app.state.settings
    return validate_init_data(init_data.strip(), settings.bot_token, max_age=settings.init_data_max_age)


def current_user(tg: TelegramUser = Depends(telegram_user), session: Session = Depends(get_session)) -> User:
    return get_or_create_user(session, tg)


# ---- рубеж 2: роль --------------------------------------------------------------------
def require_role(role: str) -> Callable[..., User]:
    def dependency(user: User = Depends(current_user), session: Session = Depends(get_session)) -> User:
        if role not in get_roles(session, user.id):
            raise AccessError("ACCESS_ROLE_REQUIRED")
        return user

    return dependency


# ---- рубеж 3: владение объектом -------------------------------------------------------
def require_owner(owner_id: int, user: User) -> None:
    """Сравнивает владельца объекта с пользователем до любого обращения к данным объекта:
    чужой и несуществующий объект неотличимы по ответу."""
    if owner_id != user.id:
        raise AccessError("ACCESS_NOT_OWNER")
