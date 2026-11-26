#!/usr/bin/env bash
# День 10. Автоматическая часть чек-листа стенда: HTTPS, /health, секреты вне репозитория, права на файлы, pg_dump.
# STAND_URL=https://... [REPO_DIR=.] [PG_DUMP_CMD="pg_dump ..."] ./stand_checklist.sh
set -uo pipefail
URL="${STAND_URL:?укажите STAND_URL}"; REPO="${REPO_DIR:-.}"; FAIL=0
ok(){ echo "[ OK ] $1"; }; bad(){ echo "[FAIL] $1"; FAIL=1; }
[[ "$URL" == https://* ]] && ok "адрес стенда по HTTPS" || bad "адрес стенда не HTTPS"
curl -fsS --max-time 10 "$URL/health" | grep -q '"ok"' && ok "/health отвечает 200" || bad "/health не отвечает"
curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "$URL/me" | grep -q 401 && ok "запрос без токена → 401" || bad "защищённый адрес открыт без токена"
curl -sS --max-time 10 "$URL/me" | grep -qiE 'traceback|File "' && bad "в ответе об ошибке виден стек" || ok "ответ об ошибке без стека"
if [ -d "$REPO/.git" ]; then
  git -C "$REPO" ls-files | grep -E '(^|/)\.env$' >/dev/null && bad ".env попал в репозиторий" || ok ".env не отслеживается git"
  git -C "$REPO" check-ignore -q .env && ok ".env в .gitignore" || bad ".env не в .gitignore"
  git -C "$REPO" log -p --all -S"BOT_TOKEN=" --oneline 2>/dev/null | grep -E '^\+BOT_TOKEN=[0-9]+:' >/dev/null && bad "токен бота найден в истории git" || ok "токен бота не найден в истории git"
fi
if [ -f "$REPO/.env" ]; then
  PERM=$(stat -c '%a' "$REPO/.env"); [[ "$PERM" =~ ^(600|640|400)$ ]] && ok "права на .env: $PERM" || bad "права на .env слишком широкие: $PERM (нужно 600)"
fi
if [ -n "${PG_DUMP_CMD:-}" ]; then
  OUT=$(mktemp); eval "$PG_DUMP_CMD" > "$OUT" 2>/dev/null; [ -s "$OUT" ] && ok "pg_dump создаёт непустой файл ($(wc -c <"$OUT") байт)" || bad "pg_dump не создал файл"; rm -f "$OUT"
fi
echo "ИТОГ: $([ $FAIL -eq 0 ] && echo ПРОЙДЕНО || echo ЕСТЬ ЗАМЕЧАНИЯ)"; exit $FAIL
