"""SQLAlchemy models for the canonical Startfind MVP data contract."""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("telegram_id", name="uq_users_telegram_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),
        CheckConstraint("role IN ('specialist', 'founder', 'admin')", name="ck_user_roles_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)


class SpecialistProfile(Base):
    __tablename__ = "specialist_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_specialist_profiles_user_id"),
        CheckConstraint("hours_per_week >= 0", name="ck_specialist_profiles_hours_per_week"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    direction: Mapped[str | None] = mapped_column(String(255))
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    portfolio: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    direction: Mapped[str] = mapped_column(String(255), nullable=False)


Index("uq_skills_name_lower", func.lower(Skill.name), unique=True)


class SpecialistSkill(Base):
    __tablename__ = "specialist_skills"
    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id", name="uq_specialist_skills_profile_skill"),
        CheckConstraint("level IN ('basic', 'confident', 'advanced')", name="ck_specialist_skills_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("specialist_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False, default="basic", server_default="basic")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'active', 'completed', 'archived')", name="ck_projects_status"),
        CheckConstraint("recruitment_status IN ('draft', 'open', 'closed')", name="ck_projects_recruitment_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    stage: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft")
    recruitment_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", server_default="draft"
    )
    last_activity_confirmation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ProjectRole(Base):
    __tablename__ = "project_roles"
    __table_args__ = (
        CheckConstraint("hours_per_week >= 0", name="ck_project_roles_hours_per_week"),
        CheckConstraint("status IN ('open', 'closed')", name="ck_project_roles_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    tasks: Mapped[str | None] = mapped_column(Text)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", server_default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class RoleSkill(Base):
    __tablename__ = "role_skills"
    __table_args__ = (
        UniqueConstraint("project_role_id", "skill_id", name="uq_role_skills_role_skill"),
        CheckConstraint("required_level IN ('basic', 'confident', 'advanced')", name="ck_role_skills_required_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_role_id: Mapped[int] = mapped_column(ForeignKey("project_roles.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    required_level: Mapped[str] = mapped_column(String(32), nullable=False, default="basic", server_default="basic")


ACTIVE_APPLICATION_STATUSES = ("sent", "viewed", "accepted", "postponed")
ACTIVE_APPLICATION_PREDICATE = "status IN ('sent', 'viewed', 'accepted', 'postponed')"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        Index(
            "uq_applications_active_profile_role",
            "specialist_profile_id",
            "project_role_id",
            unique=True,
            postgresql_where=text(ACTIVE_APPLICATION_PREDICATE),
            sqlite_where=text(ACTIVE_APPLICATION_PREDICATE),
        ),
        CheckConstraint(
            "status IN ('sent', 'viewed', 'accepted', 'rejected', 'postponed')",
            name="ck_applications_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    specialist_profile_id: Mapped[int] = mapped_column(
        ForeignKey("specialist_profiles.id", ondelete="CASCADE"), nullable=False
    )
    project_role_id: Mapped[int] = mapped_column(ForeignKey("project_roles.id", ondelete="CASCADE"), nullable=False)
    motivation: Mapped[str | None] = mapped_column(Text)
    confirmed_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="sent", server_default="sent")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'left')", name="ck_team_members_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project_role_id: Mapped[int] = mapped_column(ForeignKey("project_roles.id", ondelete="CASCADE"), nullable=False)
    specialist_profile_id: Mapped[int] = mapped_column(
        ForeignKey("specialist_profiles.id", ondelete="CASCADE"), nullable=False
    )
    tasks: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("status IN ('created', 'sent', 'failed')", name="ck_notifications_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created", server_default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


EXPECTED_TABLES = tuple(Base.metadata.tables)
