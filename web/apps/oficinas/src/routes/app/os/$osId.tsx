import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/app/os/$osId")({
  component: OSDetalhePage,
});

interface OS {
  id: string;
  numero_os: string;
  status: string;
  cliente_nome: string | null;
  veiculo_placa: string | null;
  descricao_problema: string;
  km_entrada: number | null;
  total_pecas: string;
  total_servicos: string;
  desconto: string;
  total_final: string;
  aberta_em: string;
  fechada_em: string | null;
  compartilhar_historico: boolean;
}

interface ItemOS {
  id: string;
  tipo: string;
  descricao: string;
  quantidade: string;
  preco_unitario: string;
  subtotal: string;
  produto_id: string | null;
}

interface Produto {
  id: string;
  codigo: string;
  descricao: string;
  preco_venda: string;
  estoque_atual: string;
}

const STATUS_BADGE: Record<string, "default" | "warning" | "error" | "success" | "outline"> = {
  ABERTA: "default",
  EM_EXECUCAO: "warning",
  AGUARDANDO_PECA: "error",
  FECHADA: "success",
  CANCELADA: "outline",
};

const STATUS_LABEL: Record<string, string> = {
  ABERTA: "Aberta",
  EM_EXECUCAO: "Em execução",
  AGUARDANDO_PECA: "Aguardando peça",
  FECHADA: "Fechada",
  CANCELADA: "Cancelada",
};

// Transições permitidas pelo backend
const TRANSICOES: Record<string, string[]> = {
  ABERTA: ["EM_EXECUCAO", "AGUARDANDO_PECA"],
  EM_EXECUCAO: ["AGUARDANDO_PECA"],
  AGUARDANDO_PECA: ["EM_EXECUCAO"],
};

const EDITAVEIS = new Set(["ABERTA", "EM_EXECUCAO", "AGUARDANDO_PECA"]);

function formatBRL(v: string | number) {
  return Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// ─── Formulário de adição de item ─────────────────────────────────────────────

function AdicionarItemForm({ osId, onAdded }: { osId: string; onAdded: () => void }) {
  const [tipo, setTipo] = useState<"PECA" | "SERVICO">("PECA");
  const [qProduto, setQProduto] = useState("");
  const [buscaProduto, setBuscaProduto] = useState("");
  const [produto, setProduto] = useState<Produto | null>(null);
  const [descricao, setDescricao] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [preco, setPreco] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  const { data: resultados } = useQuery({
    queryKey: ["produtos-busca-os", buscaProduto],
    queryFn: () => api.get<Produto[]>(`/produtos?q=${encodeURIComponent(buscaProduto)}`),
    enabled: buscaProduto.trim().length >= 2,
  });

  const adicionar = useMutation({
    mutationFn: () =>
      api.post(`/os/${osId}/itens`, {
        tipo,
        produto_id: tipo === "PECA" ? (produto?.id ?? null) : null,
        descricao: tipo === "PECA" ? (produto?.descricao ?? descricao) : descricao,
        quantidade: Number(quantidade),
        preco_unitario: Number(preco),
      }),
    onSuccess: () => {
      onAdded();
      setProduto(null);
      setDescricao("");
      setQuantidade("1");
      setPreco("");
      setQProduto("");
      setBuscaProduto("");
      setErro(null);
    },
    onError: (err: Error) => setErro(err.message),
  });

  const podeSalvar =
    Number(quantidade) > 0 &&
    Number(preco) >= 0 &&
    (tipo === "SERVICO" ? descricao.trim().length > 0 : produto !== null);

  return (
    <div className="border border-[--color-border] rounded-md p-4 space-y-3 bg-[--color-background]">
      <div className="flex gap-2">
        {(["PECA", "SERVICO"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => {
              setTipo(t);
              setProduto(null);
              setDescricao("");
              setPreco("");
            }}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              tipo === t
                ? "bg-[--color-primary] text-[--color-primary-fg]"
                : "bg-[--color-surface] text-[--color-text-secondary] border border-[--color-border]"
            }`}
          >
            {t === "PECA" ? "Peça" : "Serviço"}
          </button>
        ))}
      </div>

      {tipo === "PECA" ? (
        produto ? (
          <div className="flex items-center justify-between rounded border border-[--color-border] px-3 py-2">
            <div>
              <p className="text-sm font-medium text-[--color-text-primary]">{produto.descricao}</p>
              <p className="text-xs text-[--color-text-muted]">
                {produto.codigo} · estoque: {Number(produto.estoque_atual).toFixed(0)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setProduto(null);
                setPreco("");
              }}
              className="text-xs text-[--color-text-muted] hover:text-[--color-error]"
            >
              Trocar
            </button>
          </div>
        ) : (
          <>
            <div className="flex gap-2">
              <input
                value={qProduto}
                onChange={(e) => setQProduto(e.target.value)}
                placeholder="Buscar produto..."
                className="flex-1 rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
              <Button
                type="button"
                size="sm"
                disabled={qProduto.trim().length < 2}
                onClick={() => setBuscaProduto(qProduto.trim())}
              >
                Buscar
              </Button>
            </div>
            {resultados && resultados.length > 0 && (
              <div className="border border-[--color-border] rounded divide-y divide-[--color-border] max-h-48 overflow-y-auto">
                {resultados.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      setProduto(p);
                      setPreco(p.preco_venda);
                      setQProduto("");
                      setBuscaProduto("");
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-[--color-surface] flex justify-between gap-4"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[--color-text-primary] truncate">
                        {p.descricao}
                      </p>
                      <p className="text-xs text-[--color-text-muted]">{p.codigo}</p>
                    </div>
                    <span className="text-sm font-mono text-[--color-text-secondary] shrink-0">
                      {formatBRL(p.preco_venda)}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </>
        )
      ) : (
        <div className="space-y-1">
          <label htmlFor="item-desc" className="text-xs text-[--color-text-muted]">
            Descrição do serviço
          </label>
          <input
            id="item-desc"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder="Ex: Troca de óleo e filtro"
            className="w-full rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
      )}

      <div className="flex gap-3 items-end">
        <div className="space-y-0.5">
          <label htmlFor="item-qty" className="text-xs text-[--color-text-muted]">
            Qtd
          </label>
          <input
            id="item-qty"
            type="number"
            min="0.001"
            step="1"
            value={quantidade}
            onChange={(e) => setQuantidade(e.target.value)}
            className="w-20 rounded border border-[--color-border] bg-[--color-surface] px-2 py-1.5 text-sm text-right focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-0.5">
          <label htmlFor="item-price" className="text-xs text-[--color-text-muted]">
            Preço unit.
          </label>
          <input
            id="item-price"
            type="number"
            min="0"
            step="0.01"
            value={preco}
            onChange={(e) => setPreco(e.target.value)}
            className="w-28 rounded border border-[--color-border] bg-[--color-surface] px-2 py-1.5 text-sm text-right focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <Button
          type="button"
          size="sm"
          disabled={!podeSalvar || adicionar.isPending}
          onClick={() => adicionar.mutate()}
        >
          {adicionar.isPending ? "..." : "Adicionar"}
        </Button>
      </div>

      {erro && <p className="text-xs text-[--color-error]">{erro}</p>}
    </div>
  );
}

// ─── Diálogo de fechamento ────────────────────────────────────────────────────

function FecharDialog({
  osId,
  onClose,
  onFechada,
}: {
  osId: string;
  onClose: () => void;
  onFechada: () => void;
}) {
  const [compartilhar, setCompartilhar] = useState(false);
  const [resumo, setResumo] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  const fechar = useMutation({
    mutationFn: () =>
      api.post(`/os/${osId}/fechar`, {
        compartilhar_historico: compartilhar,
        resumo_publico: compartilhar && resumo ? resumo : null,
      }),
    onSuccess: () => {
      onFechada();
      onClose();
    },
    onError: (err: Error) => setErro(err.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-[--color-surface] rounded-lg shadow-lg p-6 w-full max-w-md space-y-4">
        <h2 className="text-base font-semibold text-[--color-text-primary]">Fechar OS</h2>
        <div className="flex items-center gap-2">
          <input
            id="compartilhar"
            type="checkbox"
            checked={compartilhar}
            onChange={(e) => setCompartilhar(e.target.checked)}
            className="rounded"
          />
          <label htmlFor="compartilhar" className="text-sm text-[--color-text-primary]">
            Compartilhar no histórico público do veículo
          </label>
        </div>
        {compartilhar && (
          <div className="space-y-1">
            <label htmlFor="resumo-pub" className="text-sm font-medium text-[--color-text-primary]">
              Resumo público
            </label>
            <textarea
              id="resumo-pub"
              value={resumo}
              onChange={(e) => setResumo(e.target.value)}
              rows={3}
              placeholder="O que foi feito (visível a qualquer pessoa que consultar a placa)..."
              className="w-full rounded-md border border-[--color-border] bg-[--color-background] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary] resize-none"
            />
          </div>
        )}
        {erro && <p className="text-sm text-[--color-error]">{erro}</p>}
        <div className="flex gap-2 justify-end">
          <Button type="button" size="sm" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={fechar.isPending}
            onClick={() => fechar.mutate()}
          >
            {fechar.isPending ? "Fechando..." : "Confirmar fechamento"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Página principal ─────────────────────────────────────────────────────────

function OSDetalhePage() {
  const { osId } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showFechar, setShowFechar] = useState(false);
  const [erroAcao, setErroAcao] = useState<string | null>(null);

  const { data: os, isLoading: loadingOS } = useQuery({
    queryKey: ["os", osId],
    queryFn: () => api.get<OS>(`/os/${osId}`),
  });

  const { data: itens, isLoading: loadingItens } = useQuery({
    queryKey: ["os-itens", osId],
    queryFn: () => api.get<ItemOS[]>(`/os/${osId}/itens`),
  });

  function invalidar() {
    void queryClient.invalidateQueries({ queryKey: ["os", osId] });
    void queryClient.invalidateQueries({ queryKey: ["os-itens", osId] });
    void queryClient.invalidateQueries({ queryKey: ["os"] });
  }

  const mudarStatus = useMutation({
    mutationFn: (novo_status: string) => api.patch(`/os/${osId}/status`, { novo_status }),
    onSuccess: invalidar,
    onError: (err: Error) => setErroAcao(err.message),
  });

  const cancelar = useMutation({
    mutationFn: () => api.post(`/os/${osId}/cancelar`, {}),
    onSuccess: invalidar,
    onError: (err: Error) => setErroAcao(err.message),
  });

  const removerItem = useMutation({
    mutationFn: (itemId: string) => api.delete(`/os/${osId}/itens/${itemId}`),
    onSuccess: invalidar,
    onError: (err: Error) => setErroAcao(err.message),
  });

  if (loadingOS) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (!os) {
    return (
      <div className="p-8">
        <p className="text-sm text-[--color-text-muted]">OS não encontrada.</p>
      </div>
    );
  }

  const editavel = EDITAVEIS.has(os.status);
  const proximosStatus = TRANSICOES[os.status] ?? [];

  return (
    <div className="p-8 space-y-6 max-w-3xl">
      {showFechar && (
        <FecharDialog osId={osId} onClose={() => setShowFechar(false)} onFechada={invalidar} />
      )}

      {/* ── Cabeçalho ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-[--color-text-primary]">{os.numero_os}</h1>
            <Badge variant={STATUS_BADGE[os.status] ?? "outline"}>
              {STATUS_LABEL[os.status] ?? os.status}
            </Badge>
          </div>
          <p className="text-sm text-[--color-text-muted] mt-1">
            {os.cliente_nome ?? "Cliente não identificado"}
            {os.veiculo_placa && (
              <span className="font-mono ml-2 text-[--color-text-primary]">{os.veiculo_placa}</span>
            )}
            {os.km_entrada != null && (
              <span className="ml-2">{os.km_entrada.toLocaleString()} km</span>
            )}
          </p>
          <p className="text-sm text-[--color-text-secondary] mt-0.5">{os.descricao_problema}</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => void navigate({ to: "/app/os" })}>
          ← Voltar
        </Button>
      </div>

      {/* ── Ações de status ───────────────────────────────────────────────── */}
      {editavel && (
        <Card>
          <CardContent className="py-3 flex flex-wrap items-center gap-2">
            {proximosStatus.map((s) => (
              <Button
                key={s}
                size="sm"
                variant="outline"
                disabled={mudarStatus.isPending}
                onClick={() => mudarStatus.mutate(s)}
              >
                → {STATUS_LABEL[s]}
              </Button>
            ))}
            <div className="ml-auto flex gap-2">
              <Button
                size="sm"
                onClick={() => setShowFechar(true)}
                disabled={mudarStatus.isPending || cancelar.isPending}
              >
                Fechar OS
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={cancelar.isPending}
                onClick={() => {
                  if (confirm("Cancelar esta OS? As peças reservadas serão liberadas.")) {
                    cancelar.mutate();
                  }
                }}
              >
                Cancelar OS
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {erroAcao && <p className="text-sm text-[--color-error]">{erroAcao}</p>}

      {/* ── Itens ─────────────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Itens</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loadingItens ? (
            <div className="p-4 space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : itens && itens.length > 0 ? (
            <div className="divide-y divide-[--color-border]">
              {itens.map((item) => (
                <div key={item.id} className="px-4 py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant={item.tipo === "PECA" ? "default" : "secondary"}>
                        {item.tipo === "PECA" ? "Peça" : "Serviço"}
                      </Badge>
                      <span className="text-sm font-medium text-[--color-text-primary] truncate">
                        {item.descricao}
                      </span>
                    </div>
                    <p className="text-xs text-[--color-text-muted] mt-0.5">
                      {Number(item.quantidade).toFixed(0)} × {formatBRL(item.preco_unitario)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-sm font-mono font-semibold text-[--color-text-primary]">
                      {formatBRL(item.subtotal)}
                    </span>
                    {editavel && (
                      <button
                        type="button"
                        onClick={() => removerItem.mutate(item.id)}
                        className="text-xs text-[--color-text-muted] hover:text-[--color-error] transition-colors"
                      >
                        Remover
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[--color-text-muted] py-6 text-center px-4">
              Nenhum item adicionado.
            </p>
          )}

          {editavel && (
            <div className="p-4 border-t border-[--color-border]">
              <p className="text-xs font-medium text-[--color-text-muted] mb-3">Adicionar item</p>
              <AdicionarItemForm osId={osId} onAdded={invalidar} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Totais ────────────────────────────────────────────────────────── */}
      <Card>
        <CardContent className="py-3 space-y-1">
          {(
            [
              ["Peças", os.total_pecas],
              ["Serviços", os.total_servicos],
              ["Desconto", os.desconto],
            ] as [string, string][]
          ).map(([label, val]) => (
            <div key={label} className="flex justify-between text-sm">
              <span className="text-[--color-text-muted]">{label}</span>
              <span className="font-mono text-[--color-text-secondary]">{formatBRL(val)}</span>
            </div>
          ))}
          <div className="flex justify-between text-base font-semibold border-t border-[--color-border] pt-2 mt-2">
            <span className="text-[--color-text-primary]">Total</span>
            <span className="font-mono text-[--color-text-primary]">
              {formatBRL(os.total_final)}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
