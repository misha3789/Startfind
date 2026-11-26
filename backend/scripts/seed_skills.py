"""Идемпотентная загрузка справочника навыков из docs/skills.csv (колонки name, direction).

Запуск из папки backend:
    python -m scripts.seed_skills [--csv путь] [--dry-run]

Совпадение навыков регистронезависимое (ADR-002, индекс uq_skills_name_lower): повторный запуск
ничего не дублирует. Уже существующий навык не перезаписывается, различия направления выводятся.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import make_engine, make_session_factory
from app.models import Skill

# локально: <репозиторий>/docs/skills.csv; в контейнере docs монтируется в /docs
DEFAULT_CSV = Path(__file__).resolve().parents[2] / "docs" / "skills.csv"
REQUIRED_COLUMNS = ("name", "direction")


class SeedError(Exception):
    pass


def read_rows(path: Path) -> list[tuple[str, str]]:
    """Читает и проверяет CSV: колонки, пустые значения, дубли без учёта регистра."""
    if not path.is_file():
        raise SeedError(f"файл не найден: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or any(c not in reader.fieldnames for c in REQUIRED_COLUMNS):
            raise SeedError(f"в {path} должны быть колонки {', '.join(REQUIRED_COLUMNS)}")
        rows, seen = [], {}
        for line_no, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            direction = (row.get("direction") or "").strip()
            if not name or not direction:
                raise SeedError(f"строка {line_no}: name и direction обязательны")
            key = name.lower()
            if key in seen:
                raise SeedError(f"строка {line_no}: дубль навыка «{name}» (уже в строке {seen[key]})")
            seen[key] = line_no
            rows.append((name, direction))
    if not rows:
        raise SeedError(f"{path} не содержит навыков")
    return rows


def seed(session: Session, rows: list[tuple[str, str]], *, dry_run: bool = False) -> dict[str, int]:
    """Добавляет отсутствующие навыки. Возвращает счётчики added / existing."""
    added = existing = 0
    for name, direction in rows:
        found = session.scalar(select(Skill).where(func.lower(Skill.name) == name.lower()))
        if found is None:
            session.add(Skill(name=name, direction=direction))
            added += 1
        else:
            existing += 1
            if found.direction != direction:
                print(
                    f"внимание: «{found.name}» уже есть с направлением «{found.direction}», "
                    f"в CSV «{direction}» — не меняю"
                )
    if dry_run:
        session.rollback()
    else:
        session.commit()
    return {"added": added, "existing": existing}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Загрузка справочника навыков")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--dry-run", action="store_true", help="проверить, ничего не записывая")
    args = parser.parse_args(argv)
    try:
        rows = read_rows(args.csv)
    except SeedError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    engine = make_engine(get_settings().database_url)
    try:
        with make_session_factory(engine)() as session:
            result = seed(session, rows, dry_run=args.dry_run)
    finally:
        engine.dispose()
    mode = " (пробный запуск, без записи)" if args.dry_run else ""
    print(f"Навыки: добавлено {result['added']}, уже было {result['existing']}{mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
