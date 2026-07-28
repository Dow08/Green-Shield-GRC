import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Config de test séparée de vite.config.ts : le plugin Tailwind n'a rien à faire
// dans un environnement jsdom qui ne rend jamais de CSS, et vitest n'a pas besoin
// du proxy /api de dev.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
