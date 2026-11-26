"""Add database cascades required by DELETE /me."""
from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CASCADE_FOREIGN_KEYS = (
    ("user_roles", "user_id", "users"),
    ("specialist_profiles", "user_id", "users"),
    ("specialist_skills", "profile_id", "specialist_profiles"),
    ("projects", "owner_id", "users"),
    ("project_roles", "project_id", "projects"),
    ("role_skills", "project_role_id", "project_roles"),
    ("applications", "specialist_profile_id", "specialist_profiles"),
    ("applications", "project_role_id", "project_roles"),
    ("team_members", "project_id", "projects"),
    ("team_members", "project_role_id", "project_roles"),
    ("team_members", "specialist_profile_id", "specialist_profiles"),
    ("notifications", "user_id", "users"),
)


def _constraint_name(table: str, column: str) -> str:
    return f"{table}_{column}_fkey"


def upgrade() -> None:
    for table, column, target in CASCADE_FOREIGN_KEYS:
        name = _constraint_name(table, column)
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, target, [column], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    for table, column, target in reversed(CASCADE_FOREIGN_KEYS):
        name = _constraint_name(table, column)
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, target, [column], ["id"])
