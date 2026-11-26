import { ERROR_MESSAGES, FALLBACK } from "../errorMessages.js";

/**
 * Показывает ошибку API в формате {code, message, fields, request_id}.
 * Props: error — тело ответа; onAction(action) — обработчик кнопки (reopen/addRole/retry/profile).
 */
const ACTION_LABELS = {
  reopen: "Закрыть",
  addRole: "Добавить роль",
  retry: "Повторить",
  profile: "Заполнить профиль",
};

export default function ErrorMessage({ error, onAction }) {
  if (!error) return null;
  const spec = ERROR_MESSAGES[error.code] ?? FALLBACK;
  if (spec.silent) return null;

  // Приоритет у текста сервера: в нём может быть статус отклика и номер запроса.
  const serverUsable = error.message && !(spec.dynamic && error.message.includes("…"));
  const text = serverUsable ? error.message : spec.text;
  const fields = Array.isArray(error.fields) ? error.fields : [];

  return (
    <div className="error" role="alert">
      <p>{text}</p>
      {fields.length > 0 && (
        <ul>
          {fields.map((f, i) => (
            <li key={i}>{f.field}</li>
          ))}
        </ul>
      )}
      {spec.action && onAction && (
        <button onClick={() => onAction(spec.action)}>{ACTION_LABELS[spec.action]}</button>
      )}
      {error.request_id && <small className="muted">Код обращения: {error.request_id}</small>}
    </div>
  );
}
