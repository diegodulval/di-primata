import { api } from "@/lib/api";
import { Button, Card, CardContent, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/app/fornecedores/$fornecedorId")({
  component: ProdutosFornecedorPage,
});

interface Fornecedor {
  id: string;
  razao_social: string;
  nome_fantasia: string | null;
  cnpj: string | null;
  inscricao_estadual: string | null;
  telefone: string | null;
}

interface ProdutoFornecedor {
  mapeamento_id: string;
  produto_id: string;
  codigo_interno: string;
  codigo_fornecedor: string;
  descricao: string;
  marca: string | null;
}

const PAGE_SIZE = 10;

function ProdutosFornecedorPage() {
  const { fornecedorId } = Route.useParams();
  const [q, setQ] = useState("");
  const [buscaAtiva, setBuscaAtiva] = useState("");
  const [pagina, setPagina] = useState(1);

  const { data: fornecedor, isLoading: loadingF } = useQuery({
    queryKey: ["fornecedor", fornecedorId],
    queryFn: () => api.get<Fornecedor>(`/fornecedores/${fornecedorId}`),
  });

  const { data: produtos, isLoading: loadingP } = useQuery({
    queryKey: ["fornecedor-produtos", fornecedorId, buscaAtiva],
    queryFn: () => {
      const params = buscaAtiva ? `?q=${encodeURIComponent(buscaAtiva)}` : "";
      return api.get<ProdutoFornecedor[]>(`/fornecedores/${fornecedorId}/produtos${params}`);
    },
  });

  const total = produtos?.length ?? 0;
  const totalPaginas = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const paginados = produtos?.slice((pagina - 1) * PAGE_SIZE, pagina * PAGE_SIZE) ?? [];

  function buscar() {
    setBuscaAtiva(q.trim());
    setPagina(1);
  }

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      {/* ── Breadcrumb ────────────────────────────────────────────────────── */}
      <div className="text-sm text-[--color-text-muted] flex items-center gap-1">
        <Link to="/app/fornecedores" className="hover:text-[--color-primary] transition-colors">
          Fornecedores
        </Link>
        <span>›</span>
        <span className="text-[--color-text-primary]">Produtos por Fornecedor</span>
      </div>

      {/* ── Dados do fornecedor ───────────────────────────────────────────── */}
      <Card>
        <CardContent className="py-4">
          {loadingF ? (
            <div className="space-y-2">
              <Skeleton className="h-5 w-64" />
              <Skeleton className="h-4 w-48" />
            </div>
          ) : fornecedor ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-xs text-[--color-text-muted] mb-0.5">Razão Social</p>
                <p className="font-medium text-[--color-text-primary]">{fornecedor.razao_social}</p>
              </div>
              <div>
                <p className="text-xs text-[--color-text-muted] mb-0.5">Nome Fantasia</p>
                <p className="text-[--color-text-secondary]">{fornecedor.nome_fantasia ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-[--color-text-muted] mb-0.5">CNPJ</p>
                <p className="font-mono text-[--color-text-secondary]">{fornecedor.cnpj ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-[--color-text-muted] mb-0.5">Inscrição Estadual</p>
                <p className="text-[--color-text-secondary]">
                  {fornecedor.inscricao_estadual ?? "—"}
                </p>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* ── Busca ─────────────────────────────────────────────────────────── */}
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && buscar()}
          placeholder="Pesquise pelo Código Interno, Referência do Fabricante ou Descrição"
          className="flex-1 rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <Button size="sm" onClick={buscar}>
          Buscar
        </Button>
      </div>

      {/* ── Tabela de produtos ────────────────────────────────────────────── */}
      <Card>
        <CardContent className="p-0 overflow-x-auto">
          {loadingP ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !produtos?.length ? (
            <p className="text-sm text-[--color-text-muted] py-10 text-center">
              {buscaAtiva
                ? "Nenhum produto encontrado para esta busca."
                : "Nenhum produto mapeado a este fornecedor ainda. Importe uma NF-e para criar os vínculos automaticamente."}
            </p>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[--color-border] text-xs font-medium text-[--color-text-muted] text-left">
                    <th className="px-4 py-3">Cód. Interno</th>
                    <th className="px-4 py-3">Cód. Fornecedor</th>
                    <th className="px-4 py-3">Descrição</th>
                    <th className="px-4 py-3">Marca</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[--color-border]">
                  {paginados.map((p) => (
                    <tr key={p.mapeamento_id} className="hover:bg-[var(--color-surface)] transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-[--color-text-muted]">
                        {p.codigo_interno}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-[--color-text-muted]">
                        {p.codigo_fornecedor}
                      </td>
                      <td className="px-4 py-3 text-[--color-text-primary] max-w-sm truncate">
                        {p.descricao}
                      </td>
                      <td className="px-4 py-3 text-[--color-text-secondary] text-xs">
                        {p.marca ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Paginação */}
              {totalPaginas > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-[--color-border] text-sm">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={pagina === 1}
                    onClick={() => setPagina((p) => p - 1)}
                  >
                    Anterior
                  </Button>
                  <span className="text-[--color-text-muted]">
                    Página {pagina} de {totalPaginas} — {total} produto{total !== 1 ? "s" : ""}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={pagina === totalPaginas}
                    onClick={() => setPagina((p) => p + 1)}
                  >
                    Próximo
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
