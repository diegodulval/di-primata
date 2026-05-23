import { api } from "@/lib/api";
import { Card, CardContent, Field, Input } from "@di-mata/ui";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/app/estoque/entrada/$entradaId")({
  component: EntradaPage,
});

// ── Types ──────────────────────────────────────────────────────────────────────

type ItemEntrada = {
  id: string;
  produto_id: string | null;
  codigo_fornecedor: string | null;
  quantidade: number;
  preco_unitario: number;
  icms: number;
  ipi: number;
  data_entrada: string | null;
};

type EntradaNfe = {
  id: string;
  fornecedor_id: string | null;
  chave_nfe: string | null;
  numero_nf: string | null;
  data_emissao: string | null;
  data_entrada: string | null;
  valor_total: number | null;
  status: string;
  criado_em: string;
  itens: ItemEntrada[];
};

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtBrl(val: number) {
  return val.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

// ── Página ────────────────────────────────────────────────────────────────────

function EntradaPage() {
  const { entradaId } = Route.useParams();
  const navigate = useNavigate();

  const { data: entrada, isLoading, error } = useQuery<EntradaNfe>({
    queryKey: ["entrada", entradaId],
    queryFn: () => api.get<EntradaNfe>(`/entradas/${entradaId}`),
  });

  const [dataEntradaNota, setDataEntradaNota] = useState<string>("");
  const [datasItens, setDatasItens] = useState<Record<string, string>>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  if (entrada && !initialized) {
    setInitialized(true);
    setDataEntradaNota(entrada.data_entrada ?? today());
    const initial: Record<string, string> = {};
    for (const item of entrada.itens) {
      initial[item.id] = item.data_entrada ?? today();
    }
    setDatasItens(initial);
  }

  const saveMutation = useMutation({
    mutationFn: () =>
      api.patch(`/entradas/${entradaId}`, {
        data_entrada: dataEntradaNota || null,
        itens: Object.entries(datasItens).map(([id, data_entrada]) => ({
          id,
          data_entrada: data_entrada || null,
        })),
      }),
    onSuccess: () => void navigate({ to: "/app/estoque/entradas" }),
    onError: (e: Error) => setSaveError(e.message),
  });

  const isProcessada = entrada?.status === "PROCESSADA";

  if (isLoading) {
    return <div className="p-6 text-sm text-[--color-text-muted]">Carregando...</div>;
  }

  if (error || !entrada) {
    return (
      <div className="p-6 text-sm text-[--color-error]">
        Entrada não encontrada.{" "}
        <Link to="/app/estoque/entradas" className="underline">
          Voltar
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3">
        <Link
          to="/app/estoque/entradas"
          className="text-sm text-[--color-text-muted] hover:text-[--color-text-primary] transition-colors"
        >
          ← Importar NF-e
        </Link>
        <span className="text-[--color-text-muted]">/</span>
        <span className="text-sm text-[--color-text-primary] font-medium">Editar Entrada</span>
      </div>

      {isProcessada && (
        <div className="rounded-md bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700">
          Esta entrada já foi processada e enviada ao financeiro. Visualização somente leitura.
        </div>
      )}

      {/* Dados da Nota */}
      <Card>
        <CardContent className="pt-6 space-y-5">
          <h2 className="text-sm font-semibold text-[--color-text-primary]">Dados da Nota</h2>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-xs text-[--color-text-muted] mb-1">Nota</p>
              <p className="font-medium text-[--color-text-primary]">{entrada.numero_nf ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-[--color-text-muted] mb-1">Chave de Acesso</p>
              <p className="font-mono text-xs text-[--color-text-secondary] break-all">
                {entrada.chave_nfe ?? "—"}
              </p>
            </div>
            <div>
              <p className="text-xs text-[--color-text-muted] mb-1">Data de Emissão</p>
              <p className="text-[--color-text-primary]">{entrada.data_emissao ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-[--color-text-muted] mb-1">Valor Total</p>
              <p className="font-mono text-[--color-text-primary]">
                {entrada.valor_total != null ? fmtBrl(entrada.valor_total) : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs text-[--color-text-muted] mb-1">Status</p>
              <span
                className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${
                  isProcessada
                    ? "text-emerald-700 border-emerald-200 bg-emerald-50"
                    : "text-amber-700 border-amber-200 bg-amber-50"
                }`}
              >
                {isProcessada ? "Processada" : "Aberta"}
              </span>
            </div>
          </div>

          <div className="max-w-xs">
            <Field label="Data de Entrada *">
              <Input
                type="date"
                value={dataEntradaNota}
                onChange={(e) => setDataEntradaNota(e.target.value)}
                disabled={isProcessada}
              />
            </Field>
          </div>
        </CardContent>
      </Card>

      {/* Itens */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <h2 className="text-sm font-semibold text-[--color-text-primary]">Itens</h2>

          <div className="overflow-x-auto rounded-lg border border-[--color-border]">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[--color-surface] border-b border-[--color-border] text-left text-xs font-medium text-[--color-text-muted]">
                  <th className="px-3 py-2">#</th>
                  <th className="px-3 py-2">Cód. Fornecedor</th>
                  <th className="px-3 py-2 text-right">Qtd</th>
                  <th className="px-3 py-2 text-right">Vlr. Unitário</th>
                  <th className="px-3 py-2 text-right">Total</th>
                  <th className="px-3 py-2">Dt. Entrada</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-border]">
                {entrada.itens.map((item, idx) => (
                  <tr key={item.id} className="bg-[--color-surface]">
                    <td className="px-3 py-2.5 text-[--color-text-muted] text-xs">{idx + 1}</td>
                    <td className="px-3 py-2.5 font-mono text-xs text-[--color-text-secondary]">
                      {item.codigo_fornecedor ?? "—"}
                    </td>
                    <td className="px-3 py-2.5 text-right text-[--color-text-secondary]">
                      {item.quantidade}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-[--color-text-primary]">
                      {fmtBrl(item.preco_unitario)}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-[--color-text-primary]">
                      {fmtBrl(item.quantidade * item.preco_unitario)}
                    </td>
                    <td className="px-3 py-2.5">
                      <input
                        type="date"
                        value={datasItens[item.id] ?? ""}
                        onChange={(e) =>
                          setDatasItens((prev) => ({ ...prev, [item.id]: e.target.value }))
                        }
                        disabled={isProcessada}
                        className="rounded border border-[--color-border] bg-[--color-surface] px-2 py-1 text-xs text-[--color-text-primary] disabled:opacity-60 focus:outline-none focus:ring-1 focus:ring-[--color-primary]"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-[--color-border] bg-[--color-background]">
                  <td
                    colSpan={4}
                    className="px-3 py-2.5 text-right text-xs font-medium text-[--color-text-muted]"
                  >
                    Total
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-[--color-text-primary]">
                    {entrada.valor_total != null ? fmtBrl(entrada.valor_total) : "—"}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      {!isProcessada && (
        <div className="flex items-center justify-between">
          <Link
            to="/app/estoque/entradas"
            className="px-5 py-2 rounded-md border border-[--color-border] text-sm text-[--color-text-secondary] hover:bg-[--color-background] transition-colors"
          >
            Cancelar
          </Link>

          <div className="flex items-center gap-3">
            {saveError && <p className="text-sm text-[--color-error]">{saveError}</p>}
            <button
              type="button"
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending}
              className="px-6 py-2 rounded-md bg-[--color-primary] text-[--color-primary-fg] text-sm font-medium hover:opacity-90 disabled:opacity-60 transition-opacity"
            >
              {saveMutation.isPending ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
