"""Create projects, roles, applications, team members and notifications."""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACTIVE_APPLICATION_PREDICATE = "status IN ('sent', 'viewed', 'accepted', 'postponed')"


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("recruitment_status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("last_activity_confirmation", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'archived')",
            name="ck_projects_status",
        ),
        sa.CheckConstraint(
            "recruitment_status IN ('draft', 'open', 'closed')",
            name="ck_projects_recruitment_status",
        ),
    )
    op.create_table(
        "project_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("tasks", sa.Text(), nullable=True),
        sa.Column("hours_per_week", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("hours_per_week >= 0", name="ck_project_roles_hours_per_week"),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_project_roles_status"),
    )
    op.create_table(
        "role_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_role_id", sa.Integer(), sa.ForeignKey("project_roles.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("required_level", sa.String(length=32), server_default="basic", nullable=False),
        sa.CheckConstraint(
            "required_level IN ('basic', 'confident', 'advanced')",
            name="ck_role_skills_required_level",
        ),
        sa.UniqueConstraint("project_role_id", "skill_id", name="uq_role_skills_role_skill"),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "specialist_profile_id",
            sa.Integer(),
            sa.ForeignKey("specialist_profiles.id"),
            nullable=False,
        ),
        sa.Column("project_role_id", sa.Integer(), sa.ForeignKey("project_roles.id"), nullable=False),
        sa.Column("motivation", sa.Text(), nullable=True),
        sa.Column("confirmed_hours", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="sent", nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('sent', 'viewed', 'accepted', 'rejected', 'postponed')",
            name="ck_applications_status",
        ),
    )
    op.create_index(
        "uq_applications_active_profile_role",
        "applications",
        ["specialist_profile_id", "project_role_id"],
        unique=True,
        postgresql_where=sa.text(ACTIVE_APPLICATION_PREDICATE),
        sqlite_where=sa.text(ACTIVE_APPLICATION_PREDICATE),
    )
    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("project_role_id", sa.Integer(), sa.ForeignKey("project_roles.id"), nullable=False),
        sa.Column(
            "specialist_profile_id",
            sa.Integer(),
            sa.ForeignKey("specialist_profiles.id"),
            nullable=False,
        ),
        sa.Column("tasks", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'left')", name="ck_team_members_status"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="created", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('created', 'sent', 'failed')", name="ck_notifications_status"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("team_members")
    op.drop_index("uq_applications_active_profile_role", table_name="applications")
    op.drop_table("applications")
    op.drop_table("role_skills")
    op.drop_table("project_roles")
    op.drop_table("projects")
