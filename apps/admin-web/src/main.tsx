import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/layout.css";
import "./styles/components.css";
import "./styles/account.css";

const root = document.getElementById("root");
if (!root) throw new Error("No se encontró el elemento #root.");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
