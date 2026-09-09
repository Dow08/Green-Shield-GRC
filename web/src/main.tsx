import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { Notifications } from "./components/Notifications";
import "./index.css";

// L'afficheur de notifications est monté en frère d'`<App/>`, pas en
// enveloppeur (09/09/2026) : le magasin étant externe (lib/notifications.ts),
// aucun fournisseur de contexte n'a besoin d'entourer la frontière `<Suspense>`
// d'App.tsx — donc aucun re-rendu de la vue mission à chaque notification — et
// la pile reste hors de tout ancêtre animé par framer-motion : un `transform`
// sur un ancêtre redéfinirait le bloc conteneur d'un élément `position: fixed`
// et déplacerait la pile hors de l'écran.
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
    <Notifications />
  </StrictMode>,
);
