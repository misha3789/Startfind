"""Seed справочника навыков: загрузка, идемпотентность, регистронезависимые дубли."""
import pytest
from sqlalchemy import func, select

from app.models import Skill
from scripts.seed_skills import SeedError, read_rows, seed


def count(session):
    session.expire_all()
    return session.scalar(select(func.count()).select_from(Skill))


def write_csv(tmp_path, text):
    p = tmp_path / "skills.csv"
    p.write_text(text, encoding="utf-8")
    return p


def test_seed_loads_skills(session):
    result = seed(session, [("Python", "Разработка"), ("Figma", "Дизайн")])
    assert result == {"added": 2, "existing": 0} and count(session) == 2


def test_seed_is_idempotent(session):
    rows = [("Python", "Разработка"), ("Figma", "Дизайн")]
    seed(session, rows)
    result = seed(session, rows)
    assert result == {"added": 0, "existing": 2} and count(session) == 2


def test_seed_does_not_duplicate_by_case(session):
    seed(session, [("Python", "Разработка")])
    result = seed(session, [("python", "Разработка"), ("PYTHON", "Разработка")])
    assert result["added"] == 0 and count(session) == 1


def test_dry_run_writes_nothing(session):
    seed(session, [("Python", "Разработка")], dry_run=True)
    assert count(session) == 0


def test_real_skills_csv_is_valid():
    from scripts.seed_skills import DEFAULT_CSV
    rows = read_rows(DEFAULT_CSV)
    directions = {d for _, d in rows}
    assert 10 <= len(rows) <= 15 and len(directions) == 4


def test_csv_duplicates_rejected(tmp_path):
    p = write_csv(tmp_path, "name,direction\nPython,Разработка\npython,Разработка\n")
    with pytest.raises(SeedError):
        read_rows(p)


def test_csv_requires_columns_and_values(tmp_path):
    with pytest.raises(SeedError):
        read_rows(write_csv(tmp_path, "title,dir\nPython,Разработка\n"))
    with pytest.raises(SeedError):
        read_rows(write_csv(tmp_path, "name,direction\nPython,\n"))
