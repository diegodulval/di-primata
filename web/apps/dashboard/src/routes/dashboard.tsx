import { Link, Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { useTenant } from "@di-mata/theme";

export const Route = createFileRoute("/dashboard")({
  beforeLoad: () => {
    if (!sessionStorage.getItem("access_token")) {
      throw redirect({ to: "/login" });
    }
  },
  component: DashboardLayout,
});

const NAV_ITEMS = [
  { to: "/dashboard" as const, label: "Início" },
  { to: "/dashboard/whatsapp" as const, label: "WhatsApp" },
];

function DashboardLayout() {
  const tenant = useTenant();

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
              activeProps={{ className: "block px-3 py-2 rounded-md text-sm bg-[--color-background] text-[--color-text-primary] font-medium" }}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <main className="flex-1 min-w-0 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
