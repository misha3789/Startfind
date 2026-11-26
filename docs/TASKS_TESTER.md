# Тестировщик — Безруков М. А.: статус на 26.11.2026

## Сделано

| Задача | Как и где |
|---|---|
| Шаблоны Issue/PR, CODEOWNERS, CONTRIBUTING, TEAM, README, ai-usage, .mailmap | `.github/`, `docs/`, `.mailmap`; CODEOWNERS и логин менеджера — коммит 8e9eb4d |
| Критерии приёмки Must-задач и шаблон тест-кейса | `docs/testing/acceptance-criteria.md` |
| [2] FastAPI, `/health`, конфигурация, `install_handlers`, `validate_init_data` | `backend/app/main.py`, `config.py`, `security.py`, `errors.py`; тесты `test_health`, `test_errors`, `test_init_data` |
| `pythonpath = .`, версии в `requirements.txt`, `clean_install_check.sh` | `backend/pytest.ini`, `requirements.txt`, `backend/scripts/` (CRLF → LF) |
| [10] CI: ruff + pytest + PostgreSQL | `.github/workflows/ci.yml` |
| Тесты моделей по контракту | `test_schema_matches_er`, `test_db_constraints`, `test_data_contract` — зелёные на PostgreSQL 16 |
| Приёмка этапа 1: Definition of Done, static-review | `docs/testing/definition-of-done.md`, `docs/testing/static-review.md` |
| Поправить `test_auth_roles.py` под `name` | `backend/tests/test_auth_roles.py` |
| [6] `app.access`, `POST /auth/telegram`, `POST /me/roles`, `GET /me`, `require_role`, `require_owner` | `backend/app/access.py`, `backend/app/api/auth.py` (8e9eb4d) |
| Чек-лист стенда и smoke (файлы) | `backend/scripts/stand_checklist.sh`, `backend/tests/smoke/test_stand.py`, `docs/testing/stand-checklist.md` |
| Security-проверки этапа 2 | `backend/tests/test_security_access.py` |
| Интеграционный тест «вход → роль → чтение» | `test_integration_login_then_role_then_me` |
| Реестр дефектов Д-01…Д-05 | `docs/testing/defects.md` |

## Не сделано (ждёт других или времени)

| Задача | Чего ждёт |
|---|---|
| Включить защиту `main` | зелёный CI; делается вручную в Settings → Branches |
| Issues по Д-01…Д-05 (`defect`, `sev-low`) | права gh на запись (создать вручную по `defects.md`) |
| Прогон чек-листа и smoke на реальном адресе | стенд менеджера (задача 9) |
| Тесты справочника ИС-08, ИС-09 | `GET /skills`, `GET /directions` архитектора |
| Граничные значения и тесты профиля ИС-07, 10, 29 | `PUT /me/profile` архитектора |
| Тесты удаления, фикстуры профилей | `GET /me/profile`, `DELETE /me` архитектора |
| Интеграционный тест «вход → роль → профиль → чтение» | API профиля |
| Регресс и smoke этапов 2–3, протокол приёмки этапа 3 | всё выше |
