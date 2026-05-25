import { clearSession, getPerfil, getToken } from "@/lib/auth";
import { useTenant } from "@di-mata/theme";
import { Link, Outlet, createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

export const Route = createFileRoute("/app")({
  beforeLoad: () => {
    if (!getToken()) {
      throw redirect({ to: "/login" });
    }
  },
  component: AppLayout,
});

// ─── Nav tree types ───────────────────────────────────────────────────────────

type NavLink = { type: "link"; to: string; label: string; exact?: boolean };
type NavSection = { type: "section"; label: string; children: NavNode[] };
type NavGroup = { type: "group"; label: string; children: NavNode[] };
type NavNode = NavLink | NavSection | NavGroup;

// ─── Nav renderers ────────────────────────────────────────────────────────────

function NavLinkItem({ node }: { node: NavLink }) {
  return (
    <Link
      to={node.to}
      activeOptions={{ exact: node.exact ?? false }}
      className="block px-3 py-1.5 rounded-md text-sm text-[--color-text-secondary] hover:bg-[var(--color-background)] hover:text-[--color-text-primary] transition-colors"
      activeProps={{
        className:
          "block px-3 py-1.5 rounded-md text-sm bg-[var(--color-background)] text-[--color-text-primary] font-medium",
      }}
    >
      {node.label}
    </Link>
  );
}

function NavSectionItem({ node, depth }: { node: NavSection; depth: number }) {
  return (
    <div>
      <p
        className="px-3 pt-3 pb-0.5 text-[11px] font-semibold uppercase tracking-wider text-[--color-text-muted] select-none"
        style={{ paddingLeft: `${12 + depth * 8}px` }}
      >
        {node.label}
      </p>
      <NavNodes nodes={node.children} depth={depth + 1} />
    </div>
  );
}

function NavGroupItem({ node }: { node: NavGroup }) {
  return (
    <div>
      <p className="px-3 pt-4 pb-1 text-xs font-semibold uppercase tracking-wider text-[--color-text-muted] select-none border-t border-[--color-border] mt-2">
        {node.label}
      </p>
      <NavNodes nodes={node.children} depth={1} />
    </div>
  );
}

function NavNodes({ nodes, depth = 0 }: { nodes: NavNode[]; depth?: number }) {
  return (
    <>
      {nodes.map((node, i) => {
        const key = node.type === "link" ? node.to : `${node.type}-${node.label}-${i}`;
        if (node.type === "link") {
          return (
            <div key={key} style={{ paddingLeft: `${depth * 8}px` }}>
              <NavLinkItem node={node} />
            </div>
          );
        }
        if (node.type === "section") return <NavSectionItem key={key} node={node} depth={depth} />;
        return <NavGroupItem key={key} node={node} />;
      })}
    </>
  );
}

// ─── Layout ───────────────────────────────────────────────────────────────────

function AppLayout() {
  const tenant = useTenant();
  const navigate = useNavigate();
  const perfil = getPerfil();

  useEffect(() => {
    const handler = () => {
      clearSession();
      void navigate({ to: "/login" });
    };
    window.addEventListener("auth:unauthorized", handler);
    return () => window.removeEventListener("auth:unauthorized", handler);
  }, [navigate]);

  const NAV: NavNode[] = [
    { type: "link", to: "/app", label: "Início", exact: true },
    { type: "link", to: "/app/clientes", label: "Clientes" },
    { type: "link", to: "/app/veiculos", label: "Veículos" },
    { type: "link", to: "/app/vendas", label: "Vendas / OS" },
    {
      type: "group",
      label: "Produtos",
      children: [
        { type: "link", to: "/app/estoque", label: "Listagem de produtos" },
        { type: "link", to: "/app/estoque/entradas", label: "Entrada de compra" },
      ],
    },
    { type: "link", to: "/app/fornecedores", label: "Fornecedores" },
    {
      type: "group",
      label: "Cadastrar",
      children: [
        { type: "link", to: "/app/cadastros/marcas", label: "Marcas" },
      ],
    },
    ...(perfil === "ADMIN"
      ? ([{ type: "link", to: "/app/usuarios", label: "Usuários" }] as NavNode[])
      : []),
  ];

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      <aside className="w-56 shrink-0 border-r border-[--color-border] bg-[var(--color-surface)] flex flex-col">
        <div className="px-5 py-4 border-b border-[--color-border]">
          <span className="font-semibold text-sm text-[--color-text-primary]">
            {tenant.brandName}
          </span>
        </div>
        <nav className="flex-1 px-3 py-4">
          <NavNodes nodes={NAV} />
        </nav>
        <div className="px-3 py-4 border-t border-[--color-border]">
          <button
            type="button"
            onClick={() => {
              clearSession();
              void navigate({ to: "/login" });
            }}
            className="w-full px-3 py-2 rounded-md text-sm text-left text-[--color-text-muted] hover:bg-[var(--color-background)] hover:text-[--color-error] transition-colors"
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
