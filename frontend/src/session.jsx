import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api.js";

const SessionContext = createContext(null);
export const useSession = () => useContext(SessionContext);

/** Хранит пользователя, роли и активную роль (переключатель). Вход выполняется при открытии. */
export function SessionProvider({ children }) {
  const [state, setState] = useState({ status: "loading", user: null, error: null });
  const [activeRole, setActiveRole] = useState(null);

  const login = useCallback(async () => {
    setState({ status: "loading", user: null, error: null });
    try {
      const user = await api.login();
      setState({ status: "ready", user, error: null });
      setActiveRole((prev) => (prev && user.roles.includes(prev) ? prev : user.roles[0] ?? null));
    } catch (error) {
      setState({ status: "error", user: null, error: error.body });
    }
  }, []);

  useEffect(() => {
    login();
  }, [login]);

  const addRole = useCallback(async (role) => {
    const { roles } = await api.addRole(role); // ошибка уходит вызывающему экрану
    setState((s) => ({ ...s, user: { ...s.user, roles } }));
    setActiveRole(role);
  }, []);

  const value = { ...state, activeRole, setActiveRole, addRole, retry: login };
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
