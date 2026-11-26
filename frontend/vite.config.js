import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Backend не настроен на CORS, поэтому в разработке запросы идут через прокси Vite (тот же origin).
// На стенде то же самое делает обратный прокси (см. docs/stand-deploy.md).
const backend = process.env.VITE_BACKEND_URL || "http://localhost:8000";
const paths = ["/auth", "/me", "/skills", "/directions", "/health"];

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: Object.fromEntries(paths.map((p) => [p, { target: backend, changeOrigin: true }])),
  },
});
