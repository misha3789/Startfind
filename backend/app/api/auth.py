"""Вход и выбор роли: POST /auth/telegram, GET /me, POST /me/roles (дни 7–8)."""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..access import add_role, current_user, get_roles, get_session
from ..models import User

router = APIRouter()


class RoleIn(BaseModel):
    role: Literal["specialist", "founder"]


class MeOut(BaseModel):
    id: int
    name: str
    roles: list[str]


def _me(session: Session, user: User) -> MeOut:
    return MeOut(id=user.id, name=user.name, roles=get_roles(session, user.id))


@router.post("/auth/telegram", response_model=MeOut)
def login(user: User = Depends(current_user), session: Session = Depends(get_session)) -> MeOut:
    return _me(session, user)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(current_user), session: Session = Depends(get_session)) -> MeOut:
    return _me(session, user)


@router.post("/me/roles", response_model=MeOut)
def choose_role(body: RoleIn, user: User = Depends(current_user), session: Session = Depends(get_session)) -> MeOut:
    add_role(session, user.id, body.role)
    return _me(session, user)
