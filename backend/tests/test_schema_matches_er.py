"""День 3. Сверка схемы БД с ER: таблицы, ключи, UNIQUE, CHECK."""
from sqlalchemy import inspect

from app.models import EXPECTED_TABLES

UNIQUES = {
    "users": [["telegram_id"]],
    "user_roles": [["user_id", "role"]],
    "skills": [["name_normalized"]],
    "specialist_profiles": [["user_id"]],
    "specialist_skills": [["profile_id", "skill_id"]],
    "role_skills": [["project_role_id", "skill_id"]],
    "applications": [["specialist_profile_id", "project_role_id"]],
}
FOREIGN_KEYS = {
    "user_roles": {"user_id": "users"},
    "specialist_profiles": {"user_id": "users"},
    "specialist_skills": {"profile_id": "specialist_profiles", "skill_id": "skills"},
    "projects": {"founder_id": "users"},
    "project_roles": {"project_id": "projects"},
    "role_skills": {"project_role_id": "project_roles", "skill_id": "skills"},
    "applications": {"specialist_profile_id": "specialist_profiles", "project_role_id": "project_roles"},
    "team_members": {"project_role_id": "project_roles", "user_id": "users"},
    "notifications": {"user_id": "users"},
}


def test_exactly_11_tables(engine):
    assert sorted(inspect(engine).get_table_names()) == sorted(EXPECTED_TABLES)
    assert len(EXPECTED_TABLES) == 11


def test_unique_constraints_present(engine):
    insp = inspect(engine)
    for table, expected in UNIQUES.items():
        found = [sorted(u["column_names"]) for u in insp.get_unique_constraints(table)]
        found += [sorted(i["column_names"]) for i in insp.get_indexes(table) if i.get("unique")]
        for cols in expected:
            assert sorted(cols) in found, f"{table}: нет UNIQUE{tuple(cols)}"


def test_foreign_keys_present(engine):
    insp = inspect(engine)
    for table, expected in FOREIGN_KEYS.items():
        found = {fk["constrained_columns"][0]: fk["referred_table"] for fk in insp.get_foreign_keys(table)}
        for column, target in expected.items():
            assert found.get(column) == target, f"{table}.{column} → {target}: не найден внешний ключ"
