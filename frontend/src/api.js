import { getInitData } from "./telegram.js";

/** Ошибка API в едином формате {code, message, fields, request_id}. */
export class ApiError extends Error {
  constructor(body, status) {
    super(body?.message || "Ошибка запроса");
    this.body = body;
    this.status = status;
  }
}

const initData = () => getInitData() || import.meta.env.VITE_DEV_INIT_DATA || "";

async function request(method, path, json) {
  const headers = { Authorization: `tma ${initData()}` };
  if (json !== undefined) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(path, { method, headers, body: json === undefined ? undefined : JSON.stringify(json) });
  } catch {
    // сеть недоступна: показываем как недоступность сервиса
    throw new ApiError({ code: "SYS_DB_UNAVAILABLE" }, 0);
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* пустое или не-JSON тело */
  }
  if (!res.ok) throw new ApiError(data?.code ? data : { code: "SYS_INTERNAL" }, res.status);
  return data;
}

export const api = {
  login: () => request("POST", "/auth/telegram"),   // -> {id, name, roles}
  me: () => request("GET", "/me"),                  // -> {id, name, roles}
  addRole: (role) => request("POST", "/me/roles", { role }), // -> {roles}; role: specialist | founder
};
