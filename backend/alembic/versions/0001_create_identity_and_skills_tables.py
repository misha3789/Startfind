"""Create users, roles, profiles, skills and specialist skills."""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.CheckConstraint("role IN ('specialist', 'founder', 'admin')", name="ck_user_roles_role"),
        sa.UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),
    )
    op.create_table(
        "specialist_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("direction", sa.String(length=255), nullable=True),
        sa.Column("hours_per_week", sa.Integer(), server_default="0", nullable=False),
        sa.Column("portfolio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("hours_per_week >= 0", name="ck_specialist_profiles_hours_per_week"),
        sa.UniqueConstraint("user_id", name="uq_specialist_profiles_user_id"),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("direction", sa.String(length=255), nullable=False),
    )
    op.create_index("uq_skills_name_lower", "skills", [sa.text("lower(name)")], unique=True)
    op.create_table(
        "specialist_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("specialist_profiles.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("level", sa.String(length=32), server_default="basic", nullable=False),
        sa.CheckConstraint(
            "level IN ('basic', 'confident', 'advanced')",
            name="ck_specialist_skills_level",
        ),
        sa.UniqueConstraint("profile_id", "skill_id", name="uq_specialist_skills_profile_skill"),
    )


def downgrade() -> None:
    op.drop_table("specialist_skills")
    op.drop_index("uq_skills_name_lower", table_name="skills")
    op.drop_table("skills")
    op.drop_table("specialist_profiles")
    op.drop_table("user_roles")
    op.drop_table("users")
