import { ApiError, api } from "@/lib/api";
import { Badge, Button, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { type ChangeEvent, useRef, useState } from "react";

export const Route = createFileRoute("/app/estoque/entradas")({
  component: EntradasPage,
});

interface RascunhoResumo {
  id: string;
  fornecedor_id: string | null;
  fornecedor_nome: string | null;
  numero_nf: string | null;
  chave_nfe: string | null;
  data_emissao: string | null;
  valor_total: string | null;
  status: string;
  criado_em: string;
  pendentes: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtData(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("pt-BR");
}

function fmtBrl(v: string | null): string {
  if (!v) return "—";
  return Number.parseFloat(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

const STATUS_MAP: Record<string, { label: string; variant: "success" | "warning" | "secondary" }> =
  {
    PENDENTE: { label: "Em andamento", variant: "warning" },
    CONFIRMADA: { label: "Finalizado", variant: "success" },
    CANCELADA: { label: "Cancelado", variant: "secondary" },
  };

// ─── Page ─────────────────────────────────────────────────────────────────────

function EntradasPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [erro, setErro] = useState<string | null>(null);

  const [busca, setBusca] = useState("");
  const [filtroStatus, setFiltroStatus] = useState("Todos");
  const [dataInicial, setDataInicial] = useState("");
  const [dataFinal, setDataFinal] = useState("");
  const [pagina, setPagina] = useState(1);
  const [tamPagina, setTamPagina] = useState(10);

  const { data: rascunhos, isLoading } = useQuery({
    queryKey: ["rascunhos"],
    queryFn: () => api.get<RascunhoResumo[]>("/entradas/rascunhos"),
  });

  const importar = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("arquivo", file);
      return api.postForm<{ id: string }>("/entradas/xml", form);
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["rascunhos"] });
      void navigate({ to: "/app/estoque/nfe-revisao/$rascunhoId", params: { rascunhoId: data.id } });
    },
    onError: (err: Error) =>
      setErro(
        err instanceof ApiError && err.status === 409
          ? "Esta NF-e já foi importada anteriormente."
          : err.message,
      ),
  });

  const cancelar = useMutation({
    mutationFn: (id: string) => api.delete(`/entradas/rascunhos/${id}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["rascunhos"] }),
    onError: (err: Error) => setErro(err.message),
  });

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setErro(null);
      importar.mutate(file);
      e.target.value = "";
    }
  }

  // ─── Filter ───────────────────────────────────────────────────────────────

  const filtered = (rascunhos ?? []).filter((r) => {
    if (filtroStatus !== "Todos" && STATUS_MAP[r.status]?.label !== filtroStatus) return false;
    if (busca) {
      const q = busca.toLowerCase();
      if (
        !(r.numero_nf ?? "").toLowerCase().includes(q) &&
        !(r.fornecedor_nome ?? "").toLowerCase().includes(q) &&
        !(r.chave_nfe ?? "").toLowerCase().includes(q)
      )
        return false;
    }
    if (dataInicial && r.data_emissao && r.data_emissao < dataInicial) return false;
    if (dataFinal && r.data_emissao && r.data_emissao > dataFinal) return false;
    return true;
  });

  const totalPaginas = Math.max(1, Math.ceil(filtered.length / tamPagina));
  const paginados = filtered.slice((pagina - 1) * tamPagina, pagina * tamPagina);
  const totalRegistros = rascunhos?.length ?? 0;

  function limparFiltros() {
    setBusca("");
    setFiltroStatus("Todos");
    setDataInicial("");
    setDataFinal("");
    setPagina(1);
  }

  const temFiltro = busca || filtroStatus !== "Todos" || dataInicial || dataFinal;

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="p-8 space-y-4">
      {/* Breadcrumb */}
      <p className="text-sm text-[--color-text-muted]">
        <Link to="/app" className="hover:underline">
          Início
        </Link>
        {" > "}
        <span>Produtos</span>
        {" > "}
        <span className="font-semibold text-[--color-text-primary]">Compras</span>
      </p>

      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <input ref={fileRef} type="file" accept=".xml" onChange={handleFileChange} className="hidden" />
        <Button onClick={() => fileRef.current?.click()} disabled={importar.isPending} className="shrink-0">
          {importar.isPending ? "Processando..." : "+ Nova Compra"}
        </Button>
        <input
          type="search"
          value={busca}
          onChange={(e) => { setBusca(e.target.value); setPagina(1); }}
          placeholder="Pesquisa por Compra, Nota, Pedido ou Fornecedor"
          className="flex-1 min-w-48 rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <div className="flex items-center gap-2 shrink-0">
          <label className="text-xs text-[--color-text-muted]">Status:</label>
          <select
            value={filtroStatus}
            onChange={(e) => { setFiltroStatus(e.target.value); setPagina(1); }}
            className="rounded border border-[--color-border] bg-[--color-surface] px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            {["Todos", "Em andamento", "Finalizado", "Cancelado"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Date filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-xs text-[--color-text-muted] whitespace-nowrap">Data Inicial:</label>
          <input
            type="date"
            value={dataInicial}
            onChange={(e) => { setDataInicial(e.target.value); setPagina(1); }}
            className="rounded border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-[--color-text-muted] whitespace-nowrap">Data Final:</label>
          <input
            type="date"
            value={dataFinal}
            onChange={(e) => { setDataFinal(e.target.value); setPagina(1); }}
            className="rounded border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
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

      {erro && <p className="text-sm text-[--color-error]">{erro}</p>}

      {/* Table */}
      <div className="rounded-lg border border-[--color-border] overflow-x-auto">
        <table className="w-full text-sm min-w-[800px]">
          <thead>
            <tr className="bg-[--color-surface] border-b border-[--color-border] text-xs font-medium text-[--color-text-muted] text-left">
              <th className="px-4 py-3">Dt. NF</th>
              <th className="px-4 py-3">Dt. Entrada</th>
              <th className="px-4 py-3 text-right">Compra</th>
              <th className="px-4 py-3">Tipo</th>
              <th className="px-4 py-3">Nota</th>
              <th className="px-4 py-3">Fornecedor</th>
              <th className="px-4 py-3 text-right">Valor</th>
              <th className="px-4 py-3">Status</th>
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
                  Nenhuma compra encontrada.
                </td>
              </tr>
            ) : (
              paginados.map((r) => {
                const idx = (rascunhos ?? []).findIndex((x) => x.id === r.id);
                const compraNum = totalRegistros - idx;
                const statusInfo = STATUS_MAP[r.status] ?? { label: r.status, variant: "secondary" as const };
                return (
                  <tr
                    key={r.id}
                    className="bg-[--color-surface] hover:bg-[--color-background] transition-colors"
                  >
                    <td className="px-4 py-3 text-[--color-text-secondary]">
                      {fmtData(r.data_emissao)}
                    </td>
                    <td className="px-4 py-3 text-[--color-text-secondary]">
                      {fmtData(r.criado_em)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[--color-text-muted]">
                      {compraNum}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                        XML
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[--color-text-secondary]">
                      {r.numero_nf ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-[--color-text-primary] max-w-48 truncate" title={r.fornecedor_nome ?? undefined}>
                      {r.fornecedor_nome ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-[--color-text-primary]">
                      {fmtBrl(r.valor_total)}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {r.status === "PENDENTE" && (
                          <>
                            <Link
                              to="/app/estoque/nfe-revisao/$rascunhoId"
                              params={{ rascunhoId: r.id }}
                              className="text-xs text-[--color-primary] hover:underline"
                            >
                              Revisar
                            </Link>
                            <button
                              type="button"
                              onClick={() => cancelar.mutate(r.id)}
                              disabled={cancelar.isPending}
                              className="text-xs text-[--color-error] hover:underline"
                            >
                              Cancelar
                            </button>
                          </>
                        )}
                        {r.status === "CONFIRMADA" && (
                          <Link
                            to="/app/estoque/nfe-revisao/$rascunhoId"
                            params={{ rascunhoId: r.id }}
                            className="text-xs text-[--color-text-muted] hover:underline"
                          >
                            Ver
                          </Link>
                        )}
                      </div>
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
            className="px-4 py-2 rounded border border-[--color-border] bg-[--color-surface] text-[--color-text-secondary] hover:bg-[--color-background] disabled:opacity-40 disabled:cursor-not-allowed"
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
              className="rounded border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm focus:outline-none"
            >
              {[10, 25, 50].map((n) => (
                <option key={n} value={n}>
                  {n} linhas
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            disabled={pagina === totalPaginas}
            onClick={() => setPagina((p) => p + 1)}
            className="px-4 py-2 rounded border border-[--color-border] bg-[--color-surface] text-[--color-text-secondary] hover:bg-[--color-background] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Próximo
          </button>
        </div>
      )}
    </div>
  );
}
