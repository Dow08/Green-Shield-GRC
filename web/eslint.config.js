import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      // eslint-plugin-react-hooks v7 groupe par défaut (`configs.recommended`)
      // les règles classiques ET les règles orientées React Compiler
      // (set-state-in-effect, immutability, purity...). Ce projet n'utilise
      // pas — et ne vise pas — le React Compiler : le pattern standard
      // "fetch au montage puis setState" (Settings/CopilotGRC/Projects/
      // AuditCraft) est correct ici et ne doit pas être signalé en erreur.
      // On ne retient donc que les deux règles universellement admises.
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      // Un composant/module qui prend délibérément un paramètre non utilisé
      // (props d'interface partagée, callback ignoré) reste autorisé s'il est
      // préfixé par _ ; le reste doit être un vrai signal d'erreur.
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },
  {
    // Exception documentée (CLAUDE.md) : les tests qui mockent `fetch` castent
    // leur réponse en `any` faute de pouvoir typer proprement l'API DOM native.
    files: ["**/*.test.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  }
);
