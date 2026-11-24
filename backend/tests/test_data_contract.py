"""Контрактные проверки ADR-001, не требующие готовой БД или моделей."""
import json
from pathlib import Path


CONTRACT_PATH = Path(__file__).parents[2] / "docs" / "architecture" / "data-contract.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_contains_exactly_architecture_tables():
    assert set(CONTRACT["tables"]) == {
        "users", "user_roles", "specialist_profiles", "skills", "specialist_skills",
        "projects", "project_roles", "role_skills", "applications", "team_members",
        "notifications",
    }


def test_all_foreign_keys_target_declared_tables():
    tables = CONTRACT["tables"]
    for table_name, table in tables.items():
        assert set(table["foreign_keys"]) <= set(table["columns"]), table_name
        assert set(table["foreign_keys"].values()) <= set(tables), table_name


def test_application_statuses_follow_architecture_pdf():
    statuses = CONTRACT["tables"]["applications"]["values"]["status"]
    assert statuses == ["sent", "viewed", "accepted", "rejected", "postponed"]
    assert "withdrawn" not in statuses


def test_team_member_uses_profile_and_project_links():
    table = CONTRACT["tables"]["team_members"]
    assert {"project_id", "project_role_id", "specialist_profile_id"} <= set(table["columns"])
    assert "user_id" not in table["columns"]
    assert table["foreign_keys"] == {
        "project_id": "projects",
        "project_role_id": "project_roles",
        "specialist_profile_id": "specialist_profiles",
    }


def test_profile_input_is_limited_to_architecture_fields():
    profile = CONTRACT["profile_input"]
    assert profile["fields"] == ["direction", "skills", "hours_per_week", "portfolio"]
    assert "topics" not in profile["fields"]
    assert profile["skill_fields"] == ["skill_id", "level"]


def test_pgvector_is_non_blocking_for_mvp():
    pgvector = CONTRACT["pgvector"]
    assert pgvector["required_for_mvp"] is False
    assert pgvector["vector_columns"] == []
    assert pgvector["matching_mode"] == "deterministic"
