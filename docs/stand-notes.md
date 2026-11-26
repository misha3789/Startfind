# Заметки к стенду (черновик)

- Backend не настроен на CORS. Mini App и API должны быть на одном домене: обратный прокси (Caddy/nginx)
  отдаёт `frontend/dist` и проксирует `/auth`, `/me`, `/skills`, `/directions`, `/health` на backend:8000.
- Токен бота — только в `.env` на сервере (права 600).
- После `docker compose up`: `docker compose exec backend python -m scripts.seed_skills`.
