import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// En dev, /api est proxifié vers l'API FastAPI (port 8000).
// En prod (conteneur), nginx sert le SPA et proxifie /api vers le service api.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5175,
    strictPort: true,
    proxy: {
      // IPv4 explicite : `localhost` se résout en ::1 en premier sur cette
      // machine, mais uvicorn n'écoute qu'en 127.0.0.1 — le proxy échouait
      // (connexion refusée, jamais de trace côté API) avant même d'atteindre
      // le backend, remonté au frontend comme un HTTP 500 générique.
      "/api": "http://127.0.0.1:8000",
    },
  },
});
