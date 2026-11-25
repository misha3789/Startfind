import { useState } from "react";
import { getTelegramUser, isInsideTelegram } from "./telegram.js";
import Home from "./screens/Home.jsx";
import Stub from "./screens/Stub.jsx";

// Навигация-заглушка: экраны наполняются по плану (вход и роль — день 8, профиль — день 14).
const TABS = [
  { id: "home", label: "Главная" },
  { id: "profile", label: "Профиль" },
  { id: "teams", label: "Команды" },
  { id: "settings", label: "Настройки" },
];

export default function App() {
  const [tab, setTab] = useState("home");
  const user = getTelegramUser();

  return (
    <div className="app">
      <main className="content">
        {tab === "home" ? (
          <Home userName={user?.first_name} insideTelegram={isInsideTelegram()} />
        ) : (
          <Stub title={TABS.find((t) => t.id === tab).label} />
        )}
      </main>
      <nav className="tabbar">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={t.id === tab ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
