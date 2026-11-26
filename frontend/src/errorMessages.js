// Тексты ошибок для 27 кодов. Источник: backend/app/errors.py (CATALOG).
// Если сервер прислал message (например, со статусом отклика), показываем его: он точнее.
// silent: true — ситуация фоновая, пользователю ошибка не показывается.
// dynamic: true — сервер подставляет в текст статус вместо «…»; пока в сообщении остался шаблон «…», показываем локальный текст.
// action — подсказка для кнопки: "reopen" (перезапуск), "addRole", "retry", "profile".
export const ERROR_MESSAGES = {
  AUTH_INVALID_INIT_DATA: { text: "Сессия устарела. Откройте Startfind заново из Telegram.", action: "reopen" },
  ACCESS_NOT_OWNER: { text: "Это действие доступно только автору проекта." },
  ACCESS_ROLE_REQUIRED: { text: "Это действие доступно другой роли. Добавить её в профиль?", action: "addRole" },
  VAL_APPLICATION: { text: "Напишите, чем вам интересен проект (до 500 символов), и подтвердите часы." },
  VAL_FILTER: { text: "Проверьте параметры фильтра." },
  VAL_OUT_OF_RANGE: { text: "Укажите от 1 до 40 часов в неделю и ссылку вида https://…" },
  VAL_PROJECT_INCOMPLETE: { text: "Чтобы опубликовать проект, добавьте идею, стадию и хотя бы одну роль." },
  VAL_REJECTION_REASON: { text: "Выберите причину отказа — кандидат увидит корректное сообщение." },
  VAL_REQUIRED_FIELDS: { text: "Заполните направление, навыки и часы в неделю." },
  VAL_ROLE_WITHOUT_SKILLS: { text: "Укажите хотя бы один навык для роли." },
  VAL_SKILL_NOT_IN_CATALOG: { text: "Такого навыка нет в справочнике — выберите из списка." },
  RULE_ALREADY_MEMBER: { text: "Специалист уже в команде на этой роли." },
  RULE_DUPLICATE_APPLICATION: { text: "Вы уже откликнулись на эту роль.", dynamic: true },
  RULE_INVALID_STATUS_TRANSITION: { text: "Этот отклик уже в другом статусе, действие недоступно.", dynamic: true },
  RULE_PROFILE_REQUIRED: { text: "Сначала заполните профиль — он приложится к отклику автоматически.", action: "profile" },
  RULE_PROJECT_NOT_ACTIVE: { text: "Проект сейчас не набирает участников." },
  RULE_ROLE_CLOSED: { text: "Набор на эту роль закрыт. Посмотрите другие роли проекта." },
  RULE_ROLE_HAS_MEMBERS: { text: "В этой роли есть участники — сначала завершите их участие." },
  RULE_SELF_APPLICATION: { text: "Нельзя откликнуться на роль в своём проекте." },
  NF_PROJECT: { text: "Проект больше недоступен." },
  EXT_BOT_BLOCKED: { text: "Включите бота Startfind, чтобы получать уведомления.", silent: true },
  EXT_EMBEDDING_UNAVAILABLE: { text: "Работает резервный подбор.", silent: true },
  EXT_TELEGRAM_UNAVAILABLE: { text: "Уведомление будет отправлено повторно.", silent: true },
  SYS_CONCURRENT_UPDATE: { text: "Отклик уже обработан — показываем актуальный статус." },
  SYS_DB_UNAVAILABLE: { text: "Сервис временно недоступен. Попробуйте через минуту.", action: "retry" },
  SYS_INTERNAL: { text: "Что-то пошло не так.", action: "retry" },
  SYS_TRANSACTION_FAILED: { text: "Не удалось сохранить решение. Попробуйте ещё раз.", action: "retry" },
};

export const FALLBACK = ERROR_MESSAGES.SYS_INTERNAL;
