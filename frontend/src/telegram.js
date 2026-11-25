// Обёртка над Telegram WebApp SDK. Вне Telegram (обычный браузер) работает без падений.
export const tg = window.Telegram?.WebApp ?? null;

export function initTelegram() {
  if (!tg) return;
  tg.ready();
  tg.expand();
}

export const getInitData = () => tg?.initData ?? "";
export const getTelegramUser = () => tg?.initDataUnsafe?.user ?? null;
export const isInsideTelegram = () => Boolean(tg && tg.initData);
