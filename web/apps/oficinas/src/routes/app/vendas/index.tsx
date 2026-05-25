import { api } from "@/lib/api";
import { Badge, Button, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/app/vendas/")({
  validateSearch: (search: Record<string, unknown>) => ({
    busca: typeof search.busca === "string" ? search.busca : undefined,
  }),
  component: VendasPage,
});

interface MovimentoItem {
  id: string;
  tipo: "OS" | "VENDA";
  numero: string;
  cliente_nome: string | null;
  placa: string | null;
  valor: string;
  status: string;
  criado_em: string;
  fechada_em: string | null;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmtData(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("pt-BR");
}

function fmtBrl(v: string): string {
  return Number.parseFloat(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

const STATUS_MAP: Record<string, { label: string; variant: "default" | "warning" | "error" | "success" | "secondary" | "outline" }> = {
  ABERTA:          { label: "Aberta",         variant: "default" },
  EM_EXECUCAO:     { label: "Em execução",    variant: "warning" },
  AGUARDANDO_PECA: { label: "Aguard. peça",   variant: "error" },
  FECHADA:         { label: "Fechada",         variant: "success" },
  CANCELADA:       { label: "Cancelado",       variant: "error" },
  CONCLUIDA:       { label: "Concluída",       variant: "success" },
};

const STATUS_FILTROS = [
  "Todos",
  "Aberta",
  "Em execução",
  "Aguard. peça",
  "Fechada",
  "Concluída",
  "Cancelado",
] as const;

// ─── Page ─────────────────────────────────────────────────────────────────────

function VendasPage() {
  const { busca: buscaInicial } = Route.useSearch();
  const [busca, setBusca] = useState(buscaInicial ?? "");
  const [filtroTipo, setFiltroTipo] = useState("Todos");
  const [filtroStatus, setFiltroStatus] = useState("Todos");
  const [dataInicial, setDataInicial] = useState("");
  const [dataFinal, setDataFinal] = useState("");
  const [pagina, setPagina] = useState(1);
  const [tamPagina, setTamPagina] = useState(10);

  const { data: movimentos, isLoading } = useQuery({
    queryKey: ["movimentos"],
    queryFn: () => api.get<MovimentoItem[]>("/movimentos"),
  });

  // ─── Client-side filter ────────────────────────────────────────────────────

  const filtered = (movimentos ?? []).filter((m) => {
    if (filtroTipo !== "Todos" && m.tipo !== filtroTipo) return false;
    if (filtroStatus !== "Todos") {
      const label = STATUS_MAP[m.status]?.label;
      if (label !== filtroStatus) return false;
    }
    if (busca) {
      const q = busca.toLowerCase();
      const matchNumero = m.numero.toLowerCase().includes(q);
      const matchCliente = (m.cliente_nome ?? "").toLowerCase().includes(q);
      const matchPlaca = (m.placa ?? "").toLowerCase().includes(q);
      if (!matchNumero && !matchCliente && !matchPlaca) return false;
    }
    if (dataInicial && m.criado_em < dataInicial) return false;
    if (dataFinal && m.criado_em > dataFinal) return false;
    return true;
  });

  const totalPaginas = Math.max(1, Math.ceil(filtered.length / tamPagina));
  const paginados = filtered.slice((pagina - 1) * tamPagina, pagina * tamPagina);
  const temFiltro = busca || filtroTipo !== "Todos" || filtroStatus !== "Todos" || dataInicial || dataFinal;

  function limparFiltros() {
    setBusca("");
    setFiltroTipo("Todos");
    setFiltroStatus("Todos");
    setDataInicial("");
    setDataFinal("");
    setPagina(1);
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="p-8 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Vendas / OS</h1>
        <div className="flex items-center gap-2">
          <Link to="/app/vendas/nova">
            <Button variant="outline" size="sm">+ Nova Venda</Button>
          </Link>
          <Link to="/app/os/nova" search={{}}>
            <Button size="sm">+ Nova OS</Button>
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <input
          type="search"
          value={busca}
          onChange={(e) => { setBusca(e.target.value); setPagina(1); }}
          placeholder="Buscar por número, cliente ou placa..."
          className="flex-1 min-w-48 rounded border border-[--color-border] bg-[var(--color-surface)] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <div className="flex items-center gap-2 shrink-0">
          <label className="text-xs text-[--color-text-muted]">Tipo:</label>
          <select
            value={filtroTipo}
            onChange={(e) => { setFiltroTipo(e.target.value); setPagina(1); }}
            className="rounded border border-[--color-border] bg-[var(--color-surface)] px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            {["Todos", "OS", "VENDA"].map((t) => (
              <option key={t} value={t}>{t === "VENDA" ? "Venda" : t}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <label className="text-xs text-[--color-text-muted]">Status:</label>
          <select
            value={filtroStatus}
            onChange={(e) => { setFiltroStatus(e.target.value); setPagina(1); }}
            className="rounded border border-[--color-border] bg-[var(--color-surface)] px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            {STATUS_FILTROS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* Date filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-xs text-[--color-text-muted] whitespace-nowrap">De:</label>
          <input
            type="date"
            value={dataInicial}
            onChange={(e) => { setDataInicial(e.target.value); setPagina(1); }}
            className="rounded border border-[--color-border] bg-[var(--color-surface)] px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-[--color-text-muted] whitespace-nowrap">Até:</label>
          <input
            type="date"
            value={dataFinal}
            onChange={(e) => { setDataFinal(e.target.value); setPagina(1); }}
            className="rounded border border-[--color-border] bg-[var(--color-surface)] px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        {temFiltro && (
          <button
            type="button"
            onClick={limparFiltros}
            className="text-xs text-[--color-primary] hover:underline"
          >
            Limpar filtros
          </button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg border border-[--color-border] overflow-x-auto">
        <table className="w-full text-sm min-w-[700px]">
          <thead>
            <tr className="bg-[var(--color-surface)] border-b border-[--color-border] text-xs font-medium text-[--color-text-muted] text-left">
              <th className="px-4 py-3">Tipo</th>
              <th className="px-4 py-3">Número</th>
              <th className="px-4 py-3">Cliente</th>
              <th className="px-4 py-3">Placa</th>
              <th className="px-4 py-3 text-right">Valor</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Dt. Abertura</th>
              <th className="px-4 py-3">Dt. Fechamento</th>
              <th className="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[--color-border]">
            {isLoading ? (
              [1, 2, 3, 4, 5].map((i) => (
                <tr key={i}>
                  <td colSpan={9} className="px-4 py-3">
                    <Skeleton className="h-5 w-full" />
                  </td>
                </tr>
              ))
            ) : paginados.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-10 text-center text-sm text-[--color-text-muted]">
                  Nenhum registro encontrado.
                </td>
              </tr>
            ) : (
              paginados.map((m) => {
                const statusInfo = STATUS_MAP[m.status] ?? { label: m.status, variant: "secondary" as const };
                return (
                  <tr
                    key={m.id}
                    className="bg-[var(--color-surface)] hover:bg-[var(--color-background)] transition-colors"
                  >
                    <td className="px-4 py-3">
                      {m.tipo === "OS" ? (
                        <span className="inline-flex items-center rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                          OS
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                          Venda
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[--color-text-secondary]">
                      {m.numero}
                    </td>
                    <td
                      className="px-4 py-3 text-[--color-text-primary] max-w-40 truncate"
                      title={m.cliente_nome ?? undefined}
                    >
                      {m.cliente_nome ?? "—"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[--color-text-secondary]">
                      {m.placa ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-[--color-text-primary]">
                      {fmtBrl(m.valor)}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
                    </td>
                    <td className="px-4 py-3 text-[--color-text-secondary]">
                      {fmtData(m.criado_em)}
                    </td>
                    <td className="px-4 py-3 text-[--color-text-secondary]">
                      {fmtData(m.fechada_em)}
                    </td>
                    <td className="px-4 py-3">
                      {m.tipo === "OS" && (
                        <Link
                          to="/app/os/$osId"
                          params={{ osId: m.id }}
                          className="text-xs text-[--color-primary] hover:underline"
                        >
                          Ver OS
                        </Link>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {!isLoading && filtered.length > 0 && (
        <div className="flex items-center justify-between text-sm">
          <button
            type="button"
            disabled={pagina === 1}
            onClick={() => setPagina((p) => p - 1)}
            className="px-4 py-2 rounded border border-[--color-border] bg-[var(--color-surface)] text-[--color-text-secondary] hover:bg-[var(--color-background)] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Anterior
          </button>
          <div className="flex items-center gap-3">
            <span className="text-[--color-text-muted]">
              Página {pagina} de {totalPaginas}
            </span>
            <select
              value={tamPagina}
              onChange={(e) => { setTamPagina(Number(e.target.value)); setPagina(1); }}
              className="rounded border border-[--color-border] bg-[var(--color-surface)] px-2 py-1 text-sm focus:outline-none"
            >
              {[10, 25, 50].map((n) => (
                <option key={n} value={n}>{n} linhas</option>
              ))}
            </select>
          </div>
          <button
            type="button"
            disabled={pagina === totalPaginas}
            onClick={() => setPagina((p) => p + 1)}
            className="px-4 py-2 rounded border border-[--color-border] bg-[var(--color-surface)] text-[--color-text-secondary] hover:bg-[var(--color-background)] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Próximo
          </button>
        </div>
      )}
    </div>
  );
}
