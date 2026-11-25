# Startfind
Telegram Mini App и бот для подбора специалистов в команды стартапов.

## Команда
- Аверченков П. И. — менеджер
- Лебедев А. О. — архитектор
- Безруков М. А. — тестировщик

## Стек
Python 3.11, FastAPI, SQLAlchemy, Alembic, PostgreSQL; React, Vite, Telegram WebApp SDK; pytest; Timeweb.

## Быстрый старт
Скопировать .env.example в .env, заполнить, затем docker compose up и pytest в папке backend.

## Структура
backend/ — серверная часть и тесты; frontend/ — Mini App; docs/ — документация и отчёты.

Канонический контракт данных MVP и принятые архитектурные решения описаны в
[`docs/architecture/ADR-001-data-contract.md`](docs/architecture/ADR-001-data-contract.md).

## Тесты
```
cd backend
pip install -r requirements.txt
pytest
```

## Документация
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — ветки, коммиты, pull request, Definition of Done;
- [`docs/TEAM.md`](docs/TEAM.md) — команда и области ответственности;
- [`docs/TASKS.md`](docs/TASKS.md) — задачи по ролям и дням плана;
- [`docs/ai-usage.md`](docs/ai-usage.md) — использование ИИ.
