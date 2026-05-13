import { Skeleton } from "@di-mata/ui";
import { setAuthToken } from "@di-mata/api-client";
import { clearToken, getToken } from "@di-mata/shared";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/minha-area/")({
  beforeLoad: () => {
    if (!getToken()) {
      throw redirect({ to: "/" });
    }
  },
  component: MinhaAreaPage,
});

// ── Tipos ─────────────────────────────────────────────────────────────────────

type Account = {
  id: string;
  nome: string;
  setor_primario: string;
  whatsapp_phone: string | null;
};

type Unit = {
  id: string;
  nome: string;
  tipo: string;
  area_capacidade: number | null;
};

// ── Helper ────────────────────────────────────────────────────────────────────

async function portalFetch<T>(path: string): Promise<T> {
  const token = getToken();
  const res = await fetch(path, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    clearToken();
    setAuthToken(null);
    window.location.href = "/";
  }
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json() as Promise<T>;
}

const TIPO_LABEL: Record<string, string> = {
  TALHAO: "Talhão",
  VIVEIRO: "Viveiro",
  BAIA: "Baia",
  LINHA_PRODUCAO: "Linha de Produção",
  TEAR: "Tear",
  ATELIE: "Ateliê",
  OUTRO: "Outro",
};

// ── Componente principal ──────────────────────────────────────────────────────

function MinhaAreaPage() {
  const navigate = useNavigate();

  const [account, setAccount] = useState<Account | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      portalFetch<Account>("/api/accounts/me"),
      portalFetch<Unit[]>("/api/units"),
    ])
      .then(([acc, uns]) => {
        setAccount(acc);
        setUnits(uns);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  function logout() {
    clearToken();
    setAuthToken(null);
    void navigate({ to: "/" });
  }

  return (
    <main className="min-h-screen bg-[--color-background]">
      <header className="bg-[--color-surface] border-b border-[--color-border] px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[--color-primary] flex items-center justify-center">
            <span className="text-[--color-primary-fg] font-bold text-sm">D</span>
          </div>
          <span className="font-semibold text-sm text-[--color-text-primary]">Di Mata</span>
        </div>
        <button
          type="button"
          onClick={logout}
          className="text-xs text-[--color-text-muted] hover:text-[--color-error] transition-colors"
        >
          Sair
        </button>
      </header>

      <div className="max-w-md mx-auto px-4 py-6 space-y-5">
        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5">
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-24" />
            </div>
          ) : account ? (
            <>
              <h1 className="text-lg font-bold text-[--color-text-primary]">{account.nome}</h1>
              <p className="text-sm text-[--color-text-muted] mt-0.5 capitalize">
                {account.setor_primario}
                {account.whatsapp_phone && (
                  <span className="ml-2 font-mono">{account.whatsapp_phone}</span>
                )}
              </p>
            </>
          ) : null}
        </section>

        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-3">
          <h2 className="text-sm font-semibold text-[--color-text-primary]">Rastrear produto</h2>
          <TrackInline />
        </section>

        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-3">
          <h2 className="text-sm font-semibold text-[--color-text-primary]">
            Unidades produtivas
          </h2>
          {loading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => <Skeleton key={i} className="h-10 w-full rounded-lg" />)}
            </div>
          ) : units.length === 0 ? (
            <p className="text-sm text-[--color-text-muted]">Nenhuma unidade cadastrada.</p>
          ) : (
            <ul className="space-y-2">
              {units.map((u) => (
                <li
                  key={u.id}
                  className="flex items-center justify-between rounded-lg bg-[--color-background] px-4 py-3"
                >
                  <div>
                    <div className="text-sm font-medium text-[--color-text-primary]">{u.nome}</div>
                    <div className="text-xs text-[--color-text-muted]">
                      {TIPO_LABEL[u.tipo] ?? u.tipo}
                      {u.area_capacidade != null && ` · ${u.area_capacidade} ha`}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}

function TrackInline() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");

  function handleTrack(e: React.FormEvent) {
    e.preventDefault();
    const hash = code.trim();
    if (hash) void navigate({ to: "/p/$hash", params: { hash } });
  }

  return (
    <form onSubmit={handleTrack} className="flex gap-2">
      <input
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Código do produto"
        className="flex-1 rounded-lg border border-[--color-border] px-3 py-2 text-sm bg-[--color-background] text-[--color-text-primary] placeholder:text-[--color-text-muted] focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        autoCapitalize="none"
        spellCheck={false}
      />
      <button
        type="submit"
        className="rounded-lg bg-[--color-primary] px-4 py-2 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity whitespace-nowrap"
      >
        Buscar
      </button>
    </form>
  );
}
