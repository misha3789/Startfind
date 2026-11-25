# Startfind
Telegram Mini App и бот для подбора специалистов в команды стартапов.

## Команда
- Аверченков П. И. — менеджер
- Лебедев А. О. — архитектор
- Безруков М. А. — тестировщик

## Стек
Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL; React, Vite, Telegram WebApp SDK; pytest; Timeweb.

## Среда разработки
Поддерживается Python 3.12.x (`>=3.12,<3.13`). Команда проверила проект на
Python 3.12.3 и 3.12.16. Версии backend-зависимостей зафиксированы в
`backend/requirements.txt`.

## Быстрый старт
Скопировать .env.example в .env, заполнить, затем docker compose up и pytest в папке backend.

## Структура
backend/ — серверная часть и тесты; frontend/ — Mini App; docs/ — документация и отчёты.

Канонический контракт данных MVP и принятые архитектурные решения описаны в
[`docs/architecture/ADR-001-data-contract.md`](docs/architecture/ADR-001-data-contract.md).

## Как работать
См. docs/CONTRIBUTING.md: ветки, коммиты, pull request.
