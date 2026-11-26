import { useState } from "react";
import ErrorMessage from "./components/ErrorMessage.jsx";
import RoleSwitcher from "./components/RoleSwitcher.jsx";
import Home from "./screens/Home.jsx";
import RoleSelect from "./screens/RoleSelect.jsx";
import Stub from "./screens/Stub.jsx";
import { SessionProvider, useSession } from "./session.jsx";

// Навигация-заглушка: профиль наполняется по плану (день 14).
const TABS = [
  { id: "home", label: "Главная" },
  { id: "profile", label: "Профиль" },
  { id: "teams", label: "Команды" },
  { id: "settings", label: "Настройки" },
];

function Shell() {
  const { status, user, error, activeRole, retry } = useSession();
  const [tab, setTab] = useState("home");
  const [addingRole, setAddingRole] = useState(false);

  if (status === "loading") return <main className="content muted">Загрузка…</main>;
  if (status === "error") {
    // AUTH_INVALID_INIT_DATA: открыто вне Telegram или сессия устарела
    return (
      <main className="content">
        <h1>Startfind</h1>
        <ErrorMessage error={error} onAction={retry} />
      </main>
    );
  }
  if (user.roles.length === 0) {
    return (
      <main className="content">
        <RoleSelect />
      </main>
    );
  }
  if (addingRole) {
    return (
      <main className="content">
        <RoleSelect title="Добавить роль" exclude={user.roles} onDone={() => setAddingRole(false)} />
        <button className="link" onClick={() => setAddingRole(false)}>Отмена</button>
      </main>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <RoleSwitcher onAddRole={() => setAddingRole(true)} />
      </header>
      <main className="content">
        {tab === "home" ? <Home user={user} activeRole={activeRole} /> : <Stub title={TABS.find((t) => t.id === tab).label} />}
      </main>
      <nav className="tabbar">
        {TABS.map((t) => (
          <button key={t.id} className={t.id === tab ? "tab active" : "tab"} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

export default function App() {
  return (
    <SessionProvider>
      <Shell />
    </SessionProvider>
  );
}
