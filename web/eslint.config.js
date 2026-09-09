import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
// eslint-plugin-jsx-a11y 6.10.2 déclare encore un peer eslint "^3 … ^9" alors que
// le projet est en eslint 10 ; le plugin fonctionne (flat config supportée depuis
// la 6.9). D'où le bloc `overrides` de package.json, qui aligne ce peer sur la
// version réellement installée — sans lui, `npm ci` échoue en ERESOLVE. À retirer
// dès que l'amont publiera une version couvrant eslint 10. — 09/09/2026
import jsxA11y from "eslint-plugin-jsx-a11y";
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
      "jsx-a11y": jsxA11y,
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
      // --- Accessibilité (jsx-a11y), ajouté le 09/09/2026 ---------------------
      // Un audit a relevé 172 champs de saisie pour 75 <label>, dont 100 champs
      // n'ayant qu'un `placeholder` en guise d'intitulé — violation des critères
      // WCAG 2.1 AA 1.3.1 et 3.3.2 : le placeholder disparaît dès la saisie et
      // n'est pas restitué de façon fiable par les lecteurs d'écran.
      //
      // On retient volontairement un sous-ensemble, PAS le preset `strict` : ce
      // dernier lève plusieurs centaines d'erreurs sur cette interface (menus
      // pilotés au clic, cartes cliquables), et une règle qu'on désactive au
      // premier échec ne protège plus rien.
      //
      // Règle centrale : tout <label> doit désigner un champ, par htmlFor ou par
      // imbrication (`assert: "either"` — les deux usages coexistent ici).
      // `depth: 4` couvre les champs enveloppés dans un wrapper de mise en page.
      "jsx-a11y/label-has-associated-control": ["error", { assert: "either", depth: 4 }],
      // Garde-fous ARIA : coût nul (le code était déjà conforme) et ils
      // protègent l'autre moitié du correctif — une faute de frappe dans
      // `aria-label`, ou un rôle mal posé, redeviendrait sinon invisible.
      "jsx-a11y/aria-props": "error",
      "jsx-a11y/aria-proptypes": "error",
      "jsx-a11y/aria-role": "error",
      "jsx-a11y/aria-unsupported-elements": "error",
      "jsx-a11y/role-has-required-aria-props": "error",
      "jsx-a11y/role-supports-aria-props": "error",
      "jsx-a11y/no-redundant-roles": "error",
      // Contenus alternatifs et liens : mêmes raisons, aucun écart existant.
      "jsx-a11y/alt-text": "error",
      "jsx-a11y/anchor-has-content": "error",
      "jsx-a11y/anchor-is-valid": "error",
      "jsx-a11y/heading-has-content": "error",
      "jsx-a11y/autocomplete-valid": "error",
      //
      // NON activée : `jsx-a11y/control-has-associated-label`. C'est la règle qui
      // attraperait un champ n'ayant qu'un placeholder, mais elle ne sait pas
      // résoudre l'association htmlFor entre un <label> et un champ frère : elle
      // signale donc les champs correctement étiquetés (et jusqu'aux
      // `type="hidden"` / `type="submit"`). L'activer pousserait à remplacer les
      // <label htmlFor> par des aria-label partout, ce qui serait une régression :
      // un aria-label écrase le texte visible et casse la commande vocale
      // (WCAG 2.5.3, « Label in Name »). La convention « intitulé visible relié
      // par htmlFor, sinon aria-label » reste donc à vérifier en revue.
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
