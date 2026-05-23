import { api } from "@/lib/api";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/vendas/nova")({
  component: NovaVendaPage,
});

interface Produto {
  id: string;
  codigo: string;
  descricao: string;
  preco_venda: string;
  estoque_atual: string;
}

interface CartItem {
  produto_id: string;
  descricao: string;
  codigo: string;
  quantidade: string;
  preco_unitario: string;
}

function formatBRL(value: string | number) {
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function calcTotal(itens: CartItem[]): number {
  return itens.reduce((acc, i) => {
    const qty = Number(i.quantidade) || 0;
    const price = Number(i.preco_unitario) || 0;
    return acc + qty * price;
  }, 0);
}

function NovaVendaPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [q, setQ] = useState("");
  const [busca, setBusca] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  const { data: resultados, isFetching } = useQuery({
    queryKey: ["produtos-busca", busca],
    queryFn: () => api.get<Produto[]>(`/produtos?q=${encodeURIComponent(busca)}`),
    enabled: busca.trim().length >= 2,
  });

  function handleBuscar(e: FormEvent) {
    e.preventDefault();
    setBusca(q.trim());
  }

  function adicionarAoCart(produto: Produto) {
    setCart((prev) => {
      const idx = prev.findIndex((i) => i.produto_id === produto.id);
      if (idx !== -1) {
        const next = [...prev];
        const existing = next[idx];
        if (existing) {
          next[idx] = { ...existing, quantidade: String(Number(existing.quantidade) + 1) };
        }
        return next;
      }
      return [
        ...prev,
        {
          produto_id: produto.id,
          descricao: produto.descricao,
          codigo: produto.codigo,
          quantidade: "1",
          preco_unitario: String(produto.preco_venda),
        },
      ];
    });
    setQ("");
    setBusca("");
  }

  function atualizarItem(idx: number, campo: "quantidade" | "preco_unitario", valor: string) {
    setCart((prev) => {
      const next = [...prev];
      const existing = next[idx];
      if (existing) {
        next[idx] = { ...existing, [campo]: valor };
      }
      return next;
    });
  }

  function removerItem(idx: number) {
    setCart((prev) => prev.filter((_, i) => i !== idx));
  }

  const confirmar = useMutation({
    mutationFn: () =>
      api.post("/vendas", {
        itens: cart.map((i) => ({
          produto_id: i.produto_id,
          quantidade: Number(i.quantidade),
          preco_unitario: Number(i.preco_unitario),
        })),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["vendas"] });
      void navigate({ to: "/app/vendas", search: { busca: undefined } });
    },
    onError: (err: Error) => setErro(err.message),
  });

  const total = calcTotal(cart);
  const podeConcluir = cart.length > 0 && cart.every((i) => Number(i.quantidade) > 0);

  return (
    <div className="p-8 space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Nova venda</h1>
        <Button size="sm" variant="outline" onClick={() => void navigate({ to: "/app/vendas", search: { busca: undefined } })}>
          Cancelar
        </Button>
      </div>

      {/* Busca de produto */}
      <Card>
        <CardHeader>
          <CardTitle>Buscar produto</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form onSubmit={handleBuscar} className="flex gap-2">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Código ou descrição..."
              className="flex-1 rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
            />
            <Button type="submit" size="sm" disabled={q.trim().length < 2}>
              Buscar
            </Button>
          </form>

          {isFetching && <p className="text-xs text-[--color-text-muted]">Buscando...</p>}

          {resultados && resultados.length === 0 && busca && (
            <p className="text-sm text-[--color-text-muted]">Nenhum produto encontrado.</p>
          )}

          {resultados && resultados.length > 0 && (
            <div className="border border-[--color-border] rounded-md divide-y divide-[--color-border]">
              {resultados.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => adicionarAoCart(p)}
                  className="w-full px-3 py-2 text-left hover:bg-[--color-background] transition-colors flex items-center justify-between gap-4"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[--color-text-primary] truncate">
                      {p.descricao}
                    </p>
                    <p className="text-xs text-[--color-text-muted]">
                      {p.codigo} · estoque: {Number(p.estoque_atual).toFixed(0)}
                    </p>
                  </div>
                  <span className="text-sm font-mono text-[--color-text-secondary] shrink-0">
                    {formatBRL(p.preco_venda)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Carrinho */}
      {cart.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Itens da venda</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-[--color-border]">
              {cart.map((item, idx) => (
                <div key={item.produto_id} className="px-4 py-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[--color-text-primary] truncate">
                        {item.descricao}
                      </p>
                      <p className="text-xs text-[--color-text-muted]">{item.codigo}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removerItem(idx)}
                      className="text-xs text-[--color-text-muted] hover:text-[--color-error] transition-colors shrink-0"
                    >
                      Remover
                    </button>
                  </div>
                  <div className="flex gap-3 items-center">
                    <div className="space-y-0.5">
                      <label htmlFor={`qty-${idx}`} className="text-xs text-[--color-text-muted]">
                        Qtd
                      </label>
                      <input
                        id={`qty-${idx}`}
                        type="number"
                        min="1"
                        step="1"
                        value={item.quantidade}
                        onChange={(e) => atualizarItem(idx, "quantidade", e.target.value)}
                        className="w-20 rounded-md border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm text-right focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                      />
                    </div>
                    <div className="space-y-0.5">
                      <label htmlFor={`price-${idx}`} className="text-xs text-[--color-text-muted]">
                        Preço unit.
                      </label>
                      <input
                        id={`price-${idx}`}
                        type="number"
                        min="0"
                        step="0.01"
                        value={item.preco_unitario}
                        onChange={(e) => atualizarItem(idx, "preco_unitario", e.target.value)}
                        className="w-28 rounded-md border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm text-right focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                      />
                    </div>
                    <div className="ml-auto text-right">
                      <p className="text-xs text-[--color-text-muted]">Subtotal</p>
                      <p className="text-sm font-mono font-semibold text-[--color-text-primary]">
                        {formatBRL(
                          (Number(item.quantidade) || 0) * (Number(item.preco_unitario) || 0)
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="px-4 py-3 border-t border-[--color-border] flex items-center justify-between">
              <span className="text-sm font-medium text-[--color-text-secondary]">Total</span>
              <span className="text-lg font-mono font-bold text-[--color-text-primary]">
                {formatBRL(total)}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {erro && <p className="text-sm text-[--color-error]">{erro}</p>}

      <div className="flex justify-end">
        <Button onClick={() => confirmar.mutate()} disabled={!podeConcluir || confirmar.isPending}>
          {confirmar.isPending ? "Registrando..." : "Confirmar venda"}
        </Button>
      </div>
    </div>
  );
}
