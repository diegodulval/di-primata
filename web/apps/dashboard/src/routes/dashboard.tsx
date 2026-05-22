import { setAuthToken } from "@di-mata/api-client";
import { clearToken, getToken } from "@di-mata/shared";
import { useTenant } from "@di-mata/theme";
import { Link, Outlet, createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { DomainProvider, useDomain } from "../providers/DomainProvider";

export const Route = createFileRoute("/dashboard")({
  beforeLoad: () => {
    if (!getToken()) {
      throw redirect({ to: "/login" });
    }
  },
  component: DashboardLayoutWithDomain,
});

function DashboardLayout() {
  const tenant = useTenant();
  const domain = useDomain();
  const navigate = useNavigate();

  function logout() {
    clearToken();
    setAuthToken(null);
    void navigate({ to: "/login" });
  }

  useEffect(() => {
    const handler = () => logout();
    window.addEventListener("auth:unauthorized", handler);
    return () => window.removeEventListener("auth:unauthorized", handler);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const NAV_ITEMS = [
    { to: "/dashboard" as const, label: "Início" },
    { to: "/dashboard/usuarios" as const, label: "Usuários" },
    { to: "/dashboard/registros" as const, label: domain.labels.event.plural },
    { to: "/dashboard/whatsapp" as const, label: "WhatsApp" },
    { to: "/dashboard/settings" as const, label: "Configurações" },
  ];

  return (
    <div className="flex min-h-screen bg-[--color-background]">
      <aside className="w-56 shrink-0 border-r border-[--color-border] bg-[--color-surface] flex flex-col">
        <div className="px-5 py-4 border-b border-[--color-border]">
          <span className="font-semibold text-sm text-[--color-text-primary]">
            {tenant.brandName}
          </span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: item.to === "/dashboard" }}
              className="block px-3 py-2 rounded-md text-sm text-[--color-text-secondary] hover:bg-[--color-background] hover:text-[--color-text-primary] transition-colors"
              activeProps={{
                className:
                  "block px-3 py-2 rounded-md text-sm bg-[--color-background] text-[--color-text-primary] font-medium",
              }}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="px-3 py-4 border-t border-[--color-border]">
          <button
            type="button"
            onClick={logout}
            className="w-full px-3 py-2 rounded-md text-sm text-left text-[--color-text-muted] hover:bg-[--color-background] hover:text-[--color-error] transition-colors"
          >
            Sair
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

function DashboardLayoutWithDomain() {
  return (
    <DomainProvider>
      <DashboardLayout />
    </DomainProvider>
  );
}
