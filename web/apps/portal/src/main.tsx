import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { ThemeProvider } from "@di-mata/theme";
import { routeTree } from "./routeTree.gen";
import "./styles.css";

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const rootEl = document.getElementById("root");
if (!rootEl) throw new Error("Root element não encontrado");

createRoot(rootEl).render(
  <StrictMode>
    <ThemeProvider config={{ palette: "floresta" }}>
      <RouterProvider router={router} />
    </ThemeProvider>
  </StrictMode>
);
