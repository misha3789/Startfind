export default function Home({ userName, insideTelegram }) {
  return (
    <section>
      <h1>Startfind</h1>
      <p>Подбор специалистов в команды стартапов.</p>
      <p className="muted">
        {userName ? `Привет, ${userName}!` : "Гость"}
        {!insideTelegram && " (открыто вне Telegram)"}
      </p>
    </section>
  );
}
