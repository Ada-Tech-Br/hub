import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    // Proxy apenas para /api (rotas com prefixo explícito).
    // As chamadas às rotas /auth, /users, /content usam VITE_API_URL absoluta
    // (http://localhost:8000) e passam diretamente via CORS, sem proxy.
    // Manter proxy para /auth/* causaria interceptação do callback do Google OAuth.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
