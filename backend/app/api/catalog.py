"""MVP skills catalogue endpoints."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..access import get_session
from ..errors import ValidationAppError
from ..models import Skill

router = APIRouter()
SKILL_SEARCH_LIMIT = 20


class SkillOut(BaseModel):
    id: int
    name: str
    direction: str


def _literal_search_pattern(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/skills", response_model=list[SkillOut])
def skills(
    query: str = Query(),
    session: Session = Depends(get_session),
) -> list[Skill]:
    term = query.strip()
    if len(term) < 3:
        raise ValidationAppError("VAL_FILTER", fields=[{"field": "query", "issue": "too_short", "limit": 3}])
    pattern = f"%{_literal_search_pattern(term)}%"
    statement = (
        select(Skill)
        .where(Skill.name.ilike(pattern, escape="\\"))
        .order_by(func.lower(Skill.name), Skill.id)
        .limit(SKILL_SEARCH_LIMIT)
    )
    return list(session.scalars(statement))


@router.get("/directions", response_model=list[str])
def directions(session: Session = Depends(get_session)) -> list[str]:
    statement = select(Skill.direction).distinct().order_by(Skill.direction)
    return list(session.scalars(statement))
