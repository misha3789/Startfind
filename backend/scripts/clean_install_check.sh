#!/usr/bin/env bash
# День 2/5. Проверка чистой установки: «клонировать → docker compose up → pytest» за ≤ 15 минут по README.
# Запускать на ЧИСТОЙ папке (никаких venv и .env из рабочей копии):  ./clean_install_check.sh <URL репозитория>
set -euo pipefail
REPO="${1:?укажите URL репозитория}"
WORK="$(mktemp -d)"; START=$(date +%s)
echo "[1/4] clone → $WORK"; git clone --quiet "$REPO" "$WORK/repo"; cd "$WORK/repo"
echo "[2/4] .env из примера"; [ -f .env.example ] && cp .env.example .env || echo "ВНИМАНИЕ: нет .env.example"
echo "[3/4] docker compose up"; docker compose up -d --build
for i in $(seq 1 30); do curl -fsS http://localhost:8000/health >/dev/null 2>&1 && break || sleep 2; done
curl -fsS http://localhost:8000/health && echo
echo "[4/4] pytest"; (docker compose exec -T backend pytest -q || pytest -q)
ELAPSED=$(( $(date +%s) - START ))
echo "Время: ${ELAPSED} c (порог 900 c)"; [ "$ELAPSED" -le 900 ] && echo "РЕЗУЛЬТАТ: ПРОЙДЕНО" || { echo "РЕЗУЛЬТАТ: ПРЕВЫШЕН ЛИМИТ"; exit 1; }
docker compose down -v >/dev/null 2>&1 || true
