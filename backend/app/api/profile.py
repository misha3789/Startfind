"""MVP specialist profile and account deletion endpoints."""
from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..access import current_user, get_session, require_role
from ..errors import RuleError, SystemAppError, ValidationAppError
from ..models import Skill, SpecialistProfile, SpecialistSkill, User

router = APIRouter()
SkillLevel = Literal["basic", "confident", "advanced"]


class ProfileSkill(BaseModel):
    skill_id: int
    level: SkillLevel


class ProfileData(BaseModel):
    direction: str = Field(min_length=1)
    skills: list[ProfileSkill] = Field(min_length=1)
    hours_per_week: int = Field(ge=0)
    portfolio: str | None = None


def _profile(session: Session, user_id: int) -> SpecialistProfile | None:
    return session.scalar(select(SpecialistProfile).where(SpecialistProfile.user_id == user_id))


def _profile_out(session: Session, profile: SpecialistProfile) -> ProfileData:
    statement = (
        select(SpecialistSkill)
        .where(SpecialistSkill.profile_id == profile.id)
        .order_by(SpecialistSkill.skill_id)
    )
    skills = [ProfileSkill(skill_id=item.skill_id, level=item.level) for item in session.scalars(statement)]
    return ProfileData(
        direction=profile.direction or "",
        skills=skills,
        hours_per_week=profile.hours_per_week,
        portfolio=profile.portfolio,
    )


@router.put("/me/profile", response_model=ProfileData)
def save_profile(
    body: ProfileData,
    user: User = Depends(require_role("specialist")),
    session: Session = Depends(get_session),
) -> ProfileData:
    skill_ids = [item.skill_id for item in body.skills]
    if len(skill_ids) != len(set(skill_ids)):
        raise ValidationAppError(fields=[{"field": "skills", "issue": "duplicate_skill"}])

    existing_skill_ids = set(session.scalars(select(Skill.id).where(Skill.id.in_(skill_ids))))
    missing = sorted(set(skill_ids) - existing_skill_ids)
    if missing:
        raise ValidationAppError(
            "VAL_SKILL_NOT_IN_CATALOG",
            fields=[{"field": "skills", "issue": "unknown_skill", "skill_ids": missing}],
        )

    try:
        profile = _profile(session, user.id)
        if profile is None:
            profile = SpecialistProfile(user_id=user.id)
            session.add(profile)
            session.flush()

        profile.direction = body.direction
        profile.hours_per_week = body.hours_per_week
        profile.portfolio = body.portfolio
        session.execute(delete(SpecialistSkill).where(SpecialistSkill.profile_id == profile.id))
        session.add_all(
            SpecialistSkill(profile_id=profile.id, skill_id=item.skill_id, level=item.level)
            for item in body.skills
        )
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise SystemAppError("SYS_TRANSACTION_FAILED") from None

    return _profile_out(session, profile)


@router.get("/me/profile", response_model=ProfileData)
def get_profile(
    user: User = Depends(require_role("specialist")),
    session: Session = Depends(get_session),
) -> ProfileData:
    profile = _profile(session, user.id)
    if profile is None:
        raise RuleError("RULE_PROFILE_REQUIRED")
    return _profile_out(session, profile)


@router.delete("/me", status_code=204)
def delete_me(
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Response:
    try:
        session.delete(user)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise SystemAppError("SYS_TRANSACTION_FAILED") from None
    return Response(status_code=204)
