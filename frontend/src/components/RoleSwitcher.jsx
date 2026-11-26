import { ROLE_LABELS } from "../screens/RoleSelect.jsx";
import { useSession } from "../session.jsx";

/** Переключатель активной роли; при одной роли кнопка «+ роль» открывает её добавление. */
export default function RoleSwitcher({ onAddRole }) {
  const { user, activeRole, setActiveRole } = useSession();
  const missing = Object.keys(ROLE_LABELS).filter((r) => !user.roles.includes(r));
  return (
    <div className="roles">
      {user.roles.map((role) => (
        <button key={role} className={role === activeRole ? "chip active" : "chip"} onClick={() => setActiveRole(role)}>
          {ROLE_LABELS[role] ?? role}
        </button>
      ))}
      {missing.length > 0 && (
        <button className="chip" onClick={onAddRole}>
          + роль
        </button>
      )}
    </div>
  );
}
