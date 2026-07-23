import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// En dev, /api est proxifié vers l'API FastAPI (port 8000).
// En prod (conteneur), nginx sert le SPA et proxifie /api vers le service api.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
