import { useState } from "react";
import ErrorMessage from "../components/ErrorMessage.jsx";
import { useSession } from "../session.jsx";

export const ROLE_LABELS = { specialist: "Специалист", founder: "Основатель" };
const ROLE_HINTS = {
  specialist: "Ищу проект, в котором могу применить свои навыки",
  founder: "У меня есть идея и нужна команда",
};

/** Первый вход (ролей нет) или добавление второй роли (FR-02). */
export default function RoleSelect({ onDone, title = "Кто вы в Startfind?", exclude = [] }) {
  const { addRole } = useSession();
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);

  async function choose(role) {
    setBusy(role);
    setError(null);
    try {
      await addRole(role);
      onDone?.();
    } catch (e) {
      setError(e.body ?? { code: "SYS_INTERNAL" });
    } finally {
      setBusy(null);
    }
  }

  return (
    <section>
      <h1>{title}</h1>
      <p className="muted">Позже можно добавить вторую роль — новый аккаунт не нужен.</p>
      {Object.keys(ROLE_LABELS)
        .filter((r) => !exclude.includes(r))
        .map((role) => (
          <button key={role} className="card" disabled={busy !== null} onClick={() => choose(role)}>
            <strong>{ROLE_LABELS[role]}</strong>
            <span className="muted">{ROLE_HINTS[role]}</span>
          </button>
        ))}
      <ErrorMessage error={error} />
    </section>
  );
}
