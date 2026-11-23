"""День 3. Сверка схемы БД с каноническим контрактом ADR-001."""
import json
from pathlib import Path

from sqlalchemy import inspect

from app.models import EXPECTED_TABLES

CONTRACT_PATH = Path(__file__).parents[2] / "docs" / "architecture" / "data-contract.json"
TABLES = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["tables"]
UNIQUES = {name: table["unique"] for name, table in TABLES.items() if table["unique"]}
FOREIGN_KEYS = {name: table["foreign_keys"] for name, table in TABLES.items() if table["foreign_keys"]}


def test_exactly_11_tables(engine):
    assert set(EXPECTED_TABLES) == set(TABLES)
    assert set(inspect(engine).get_table_names()) == set(TABLES)


def test_columns_match_contract(engine):
    insp = inspect(engine)
    for table_name, table in TABLES.items():
        actual = {column["name"] for column in insp.get_columns(table_name)}
        assert actual == set(table["columns"]), f"{table_name}: колонки не совпадают с ADR-001"


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
