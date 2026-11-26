# Настройка Telegram-бота и Mini App

Выполняет менеджер. Токен бота — секрет: в репозиторий не попадает (`.env` в `.gitignore`).

## 1. Создать бота
1. В Telegram открыть @BotFather, команда `/newbot`.
2. Указать отображаемое имя (например, `Startfind`) и username, заканчивающийся на `bot` (например, `startfind_team_bot`).
3. BotFather пришлёт токен вида `123456789:AA...`. Сохранить его только в `.env` (`BOT_TOKEN=`).

## 2. Описание бота (по желанию)
`/setdescription`, `/setabouttext`, `/setuserpic` — выбрать бота и ввести текст.

## 3. Кнопка Mini App
Нужен HTTPS-адрес фронтенда. Для локальной проверки — туннель (cloudflared / ngrok), для стенда — домен из задачи «Стенд».
1. `/setmenubutton` → выбрать бота → указать URL Mini App → название кнопки (например, «Открыть»).
2. Для прямой ссылки: `/newapp` → выбрать бота → название, описание, картинка 640×360, URL, short name. Ссылка: `https://t.me/<bot_username>/<short_name>`.
3. При смене адреса (локальный → стенд) повторить `/setmenubutton`.

## 4. Заполнить .env
```
cp .env.example .env
```
| Переменная | Значение |
|---|---|
| `BOT_TOKEN` | токен от BotFather |
| `DATABASE_URL` | для локального запуска без docker — как в `.env.example`; в docker compose переопределяется на хост `db` |
| `INIT_DATA_MAX_AGE` | срок жизни initData в секундах, по умолчанию 86400 |

## 5. Проверка
- Открыть бота, нажать кнопку меню — Mini App открывается внутри Telegram.
- Backend проверяет подпись initData по `BOT_TOKEN`. Если токен перевыпущен (`/revoke`), обновить `.env` и перезапустить backend.

## Безопасность
- Токен не отправлять в чаты и Issues. При утечке: `/revoke` в BotFather и обновить `.env` на всех стендах.
