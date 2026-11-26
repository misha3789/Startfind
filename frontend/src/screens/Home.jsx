import { ROLE_LABELS } from "./RoleSelect.jsx";

export default function Home({ user, activeRole }) {
  return (
    <section>
      <h1>Привет, {user.name}!</h1>
      <p className="muted">Активная роль: {ROLE_LABELS[activeRole] ?? activeRole}</p>
      <p>Профиль и подбор проектов появятся в следующих версиях.</p>
    </section>
  );
}
