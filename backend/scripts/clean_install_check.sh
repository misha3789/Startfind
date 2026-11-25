#!/usr/bin/env bash
# День 2/5. Проверка чистой установки: «клонировать → docker compose up → pytest» за ≤ 15 минут по README.
# Запуск из любой папки (ничего из рабочей копии не используется): ./clean_install_check.sh <URL репозитория>
# Предполагает: сервис в docker-compose.yml называется backend и слушает порт 8000 (GET /health).
set -euo pipefail
REPO="${1:?укажите URL репозитория}"
WORK="$(mktemp -d)"; START=$(date +%s)
cleanup() { [ -d "$WORK/repo" ] && (cd "$WORK/repo" && docker compose down -v >/dev/null 2>&1); rm -rf "$WORK"; return 0; }
trap cleanup EXIT
trap 'echo "РЕЗУЛЬТАТ: НЕ ПРОЙДЕНО"' ERR
echo "[1/4] clone → $WORK"; git clone --quiet "$REPO" "$WORK/repo"; cd "$WORK/repo"
echo "[2/4] .env из примера"; cp .env.example .env
echo "[3/4] docker compose up"; docker compose up -d --build
ok=0; for _ in $(seq 1 30); do curl -fsS http://localhost:8000/health >/dev/null 2>&1 && { ok=1; break; } || sleep 2; done
[ "$ok" = 1 ] || { echo "ОШИБКА: /health не ответил за 60 с"; false; }
curl -fsS http://localhost:8000/health; echo
echo "[4/4] pytest"; docker compose exec -T backend pytest -q
ELAPSED=$(( $(date +%s) - START ))
echo "Время: ${ELAPSED} c (порог 900 c)"
[ "$ELAPSED" -le 900 ] && echo "РЕЗУЛЬТАТ: ПРОЙДЕНО" || { echo "РЕЗУЛЬТАТ: ПРЕВЫШЕН ЛИМИТ"; exit 1; }
