import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/estoque/")({
  component: EstoquePage,
});

interface Produto {
  id: string;
  codigo: string;
  descricao: string;
  marca: string | null;
  localizacao: string | null;
  preco_venda: string;
  estoque_atual: string;
  estoque_minimo: string;
  ativo: boolean;
}

function NovoProdutoForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [codigo, setCodigo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [marca, setMarca] = useState("");
  const [precoCusto, setPrecoCusto] = useState("");
  const [precoVenda, setPrecoVenda] = useState("");
  const [error, setError] = useState<string | null>(null);

  const criar = useMutation({
    mutationFn: () =>
      api.post("/produtos", {
        codigo,
        descricao,
        marca: marca || null,
        preco_custo: precoCusto ? Number(precoCusto) : 0,
        preco_venda: precoVenda ? Number(precoVenda) : 0,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["produtos"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Novo produto</CardTitle>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            criar.mutate();
          }}
          className="space-y-3"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label
                htmlFor="np-codigo"
                className="text-sm font-medium text-[--color-text-primary]"
              >
                Código *
              </label>
              <input
                id="np-codigo"
                required
                value={codigo}
                onChange={(e) => setCodigo(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="np-marca" className="text-sm font-medium text-[--color-text-primary]">
                Marca
              </label>
              <input
                id="np-marca"
                value={marca}
                onChange={(e) => setMarca(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1 sm:col-span-2">
              <label htmlFor="np-desc" className="text-sm font-medium text-[--color-text-primary]">
                Descrição *
              </label>
              <input
                id="np-desc"
                required
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="np-custo" className="text-sm font-medium text-[--color-text-primary]">
                Preço de custo
              </label>
              <input
                id="np-custo"
                type="number"
                min="0"
                step="0.01"
                value={precoCusto}
                onChange={(e) => setPrecoCusto(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="np-venda" className="text-sm font-medium text-[--color-text-primary]">
                Preço de venda
              </label>
              <input
                id="np-venda"
                type="number"
                min="0"
                step="0.01"
                value={precoVenda}
                onChange={(e) => setPrecoVenda(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
          </div>
          {error && <p className="text-sm text-[--color-error]">{error}</p>}
          <div className="flex gap-2 justify-end">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={criar.isPending}>
              {criar.isPending ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function EstoquePage() {
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);

  const { data: produtos, isLoading } = useQuery({
    queryKey: ["produtos", q],
    queryFn: () => api.get<Produto[]>(`/produtos${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Estoque</h1>
        <div className="flex gap-2">
          <Link to="/app/estoque/entradas">
            <Button variant="outline" size="sm">
              Importar NF-e
            </Button>
          </Link>
          <Button size="sm" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancelar" : "+ Novo produto"}
          </Button>
        </div>
      </div>

      {showForm && <NovoProdutoForm onClose={() => setShowForm(false)} />}

      <div className="mb-4">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar por código ou descrição..."
          className="w-full max-w-sm rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
      </div>

      <Card>
        <CardContent className="pt-4">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : produtos?.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] py-4 text-center">
              Nenhum produto encontrado.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[--color-border] text-left text-[--color-text-muted]">
                  <th className="pb-2 pr-4 font-medium">Código</th>
                  <th className="pb-2 pr-4 font-medium">Descrição</th>
                  <th className="pb-2 pr-4 font-medium hidden sm:table-cell">Marca</th>
                  <th className="pb-2 pr-4 font-medium text-right">Estoque</th>
                  <th className="pb-2 font-medium text-right hidden md:table-cell">Venda (R$)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-border]">
                {produtos?.map((p) => {
                  const atual = Number.parseFloat(p.estoque_atual);
                  const minimo = Number.parseFloat(p.estoque_minimo);
                  const baixo = minimo > 0 && atual <= minimo;

                  return (
                    <tr key={p.id} className={!p.ativo ? "opacity-50" : ""}>
                      <td className="py-3 pr-4 font-mono text-xs text-[--color-text-secondary]">
                        {p.codigo}
                      </td>
                      <td className="py-3 pr-4 text-[--color-text-primary]">
                        {p.descricao}
                        {!p.ativo && (
                          <Badge variant="secondary" className="ml-2 text-xs">
                            Inativo
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 pr-4 text-[--color-text-secondary] hidden sm:table-cell">
                        {p.marca ?? "—"}
                      </td>
                      <td className="py-3 pr-4 text-right">
                        <span
                          className={
                            baixo
                              ? "text-[--color-error] font-medium"
                              : "text-[--color-text-primary]"
                          }
                        >
                          {atual.toFixed(3)}
                        </span>
                        {baixo && (
                          <Badge variant="error" className="ml-2 text-xs">
                            Baixo
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 text-right text-[--color-text-secondary] hidden md:table-cell">
                        {Number.parseFloat(p.preco_venda).toLocaleString("pt-BR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
