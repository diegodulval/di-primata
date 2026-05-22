import { ApiError, api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/app/estoque/nfe-revisao/$rascunhoId")({
  component: NfeRevisaoPage,
});

// ─── Types ────────────────────────────────────────────────────────────────────

type StatusItem = "AUTO_VINCULADO" | "VINCULADO" | "NOVO" | "PENDENTE";
type StatusRascunho = "PENDENTE" | "CONFIRMADA" | "CANCELADA";

interface ItemRascunho {
  id: string;
  produto_id: string | null;
  codigo_fornecedor: string;
  codigo_ref: string | null;
  ean: string | null;
  descricao_nfe: string;
  ncm: string | null;
  quantidade: string;
  preco_unitario: string;
  icms: string;
  ipi: string;
  status_item: StatusItem;
}

interface Rascunho {
  id: string;
  fornecedor_id: string | null;
  chave_nfe: string | null;
  numero_nf: string | null;
  data_emissao: string | null;
  valor_total: string | null;
  status: StatusRascunho;
  criado_em: string;
  itens: ItemRascunho[];
  pendentes: number;
}

interface ProdutoOpcao {
  id: string;
  codigo: string;
  descricao: string;
  estoque_atual: string;
}

interface ProdutoDetalhe {
  id: string;
  codigo: string;
  descricao: string;
  marca: string | null;
  preco_custo: string;
  preco_venda: string;
  estoque_atual: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const ITEM_STATUS_BADGE: Record<
  StatusItem,
  { label: string; variant: "success" | "warning" | "secondary" | "default" }
> = {
  AUTO_VINCULADO: { label: "Auto-vinculado", variant: "success" },
  VINCULADO: { label: "Vinculado", variant: "success" },
  NOVO: { label: "Produto criado", variant: "success" },
  PENDENTE: { label: "Pendente", variant: "warning" },
};

function fmtQtd(v: string) {
  return Number.parseFloat(v).toLocaleString("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3,
  });
}

function fmtBrl(v: string | null) {
  if (!v) return "—";
  return `R$ ${Number.parseFloat(v).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;
}

// ─── Editar produto inline ────────────────────────────────────────────────────

interface EditarProdutoProps {
  produtoId: string;
  onDone: () => void;
}

function EditarProdutoPanel({ produtoId, onDone }: EditarProdutoProps) {
  const queryClient = useQueryClient();
  const [descricao, setDescricao] = useState("");
  const [marca, setMarca] = useState("");
  const [precoCusto, setPrecoCusto] = useState("");
  const [precoVenda, setPrecoVenda] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  const { data: produto, isLoading } = useQuery({
    queryKey: ["produto", produtoId],
    queryFn: () => api.get<ProdutoDetalhe>(`/produtos/${produtoId}`),
  });

  useEffect(() => {
    if (produto) {
      setDescricao(produto.descricao);
      setMarca(produto.marca ?? "");
      setPrecoCusto(produto.preco_custo);
      setPrecoVenda(produto.preco_venda);
    }
  }, [produto]);

  const salvar = useMutation({
    mutationFn: () =>
      api.patch(`/produtos/${produtoId}`, {
        descricao: descricao || undefined,
        marca: marca || null,
        preco_custo: precoCusto ? Number(precoCusto) : undefined,
        preco_venda: precoVenda ? Number(precoVenda) : undefined,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["produto", produtoId] });
      void queryClient.invalidateQueries({ queryKey: ["produtos"] });
      setErro(null);
      onDone();
    },
    onError: (err: Error) => setErro(err.message),
  });

  if (isLoading) {
    return <Skeleton className="h-24 w-full" />;
  }

  if (!produto) return null;

  return (
    <div className="space-y-3">
      <p className="text-xs text-[--color-text-muted]">
        Produto: <span className="font-mono text-[--color-text-secondary]">{produto.codigo}</span>
        {" · "}estq. atual: {fmtQtd(produto.estoque_atual)}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="sm:col-span-2 space-y-1">
          <label htmlFor="ep-descricao" className="text-xs font-medium text-[--color-text-primary]">
            Descrição
          </label>
          <input
            id="ep-descricao"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            className="w-full rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="ep-marca" className="text-xs font-medium text-[--color-text-primary]">
            Marca
          </label>
          <input
            id="ep-marca"
            value={marca}
            onChange={(e) => setMarca(e.target.value)}
            placeholder="—"
            className="w-full rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label htmlFor="ep-custo" className="text-xs font-medium text-[--color-text-primary]">
              Custo (R$)
            </label>
            <input
              id="ep-custo"
              type="number"
              min="0"
              step="0.01"
              value={precoCusto}
              onChange={(e) => setPrecoCusto(e.target.value)}
              className="w-full rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="ep-venda" className="text-xs font-medium text-[--color-text-primary]">
              Venda (R$)
            </label>
            <input
              id="ep-venda"
              type="number"
              min="0"
              step="0.01"
              value={precoVenda}
              onChange={(e) => setPrecoVenda(e.target.value)}
              className="w-full rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
            />
          </div>
        </div>
      </div>

      {erro && <p className="text-xs text-[--color-error]">{erro}</p>}

      <div className="flex gap-2">
        <Button size="sm" disabled={!descricao || salvar.isPending} onClick={() => salvar.mutate()}>
          {salvar.isPending ? "Salvando..." : "Salvar"}
        </Button>
        <Button size="sm" variant="outline" onClick={onDone}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}

// ─── Resolver inline ──────────────────────────────────────────────────────────

interface ResolverProps {
  rascunhoId: string;
  item: ItemRascunho;
  onDone: () => void;
}

function ResolverItem({ rascunhoId, item, onDone }: ResolverProps) {
  const [acao, setAcao] = useState<"vincular" | "criar_novo" | null>(null);
  const [busca, setBusca] = useState(item.codigo_ref ?? "");
  const [produtoId, setProdutoId] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const { data: produtos } = useQuery({
    queryKey: ["produtos", busca],
    queryFn: () =>
      api.get<ProdutoOpcao[]>(`/produtos${busca ? `?q=${encodeURIComponent(busca)}` : ""}`),
    enabled: acao === "vincular",
  });

  const vincular = useMutation({
    mutationFn: (payload: { acao: "vincular" | "criar_novo"; produto_id?: string }) =>
      api.patch(`/entradas/rascunhos/${rascunhoId}/itens/${item.id}`, payload),
    onSuccess: () => {
      setErro(null);
      onDone();
    },
    onError: (err: Error) => setErro(err.message),
  });

  if (acao === null) {
    return (
      <div className="flex gap-2 flex-wrap">
        <Button size="sm" variant="outline" onClick={() => setAcao("vincular")}>
          Vincular produto
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={vincular.isPending}
          onClick={() => {
            setAcao("criar_novo");
            vincular.mutate({ acao: "criar_novo" });
          }}
        >
          Criar produto
        </Button>
      </div>
    );
  }

  if (acao === "criar_novo") {
    return (
      <p className="text-xs text-[--color-text-muted]">
        {vincular.isPending ? "Criando produto..." : "Produto criado."}
      </p>
    );
  }

  // acao === "vincular"
  return (
    <div className="space-y-2 mt-1">
      <input
        type="search"
        value={busca}
        onChange={(e) => {
          setBusca(e.target.value);
          setProdutoId(null);
        }}
        placeholder="Buscar por código ou descrição..."
        className="w-full max-w-sm rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
      />
      {produtos && produtos.length > 0 && (
        <div className="border border-[--color-border] rounded-md overflow-hidden max-h-48 overflow-y-auto">
          {produtos.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setProdutoId(p.id)}
              className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between gap-4 hover:bg-[--color-background] transition-colors ${
                produtoId === p.id ? "bg-[--color-background] font-medium" : ""
              }`}
            >
              <span>
                <span className="font-mono text-xs text-[--color-text-muted] mr-2">{p.codigo}</span>
                {p.descricao}
              </span>
              <span className="text-xs text-[--color-text-muted] shrink-0">
                estq. {fmtQtd(p.estoque_atual)}
              </span>
            </button>
          ))}
        </div>
      )}
      {produtos?.length === 0 && busca && (
        <p className="text-xs text-[--color-text-muted]">Nenhum produto encontrado.</p>
      )}
      {erro && <p className="text-xs text-[--color-error]">{erro}</p>}
      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={!produtoId || vincular.isPending}
          onClick={() => {
            if (produtoId) vincular.mutate({ acao: "vincular", produto_id: produtoId });
          }}
        >
          {vincular.isPending ? "Salvando..." : "Confirmar vínculo"}
        </Button>
        <Button size="sm" variant="outline" onClick={() => setAcao(null)}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}

// ─── Página principal ─────────────────────────────────────────────────────────

function NfeRevisaoPage() {
  const { rascunhoId } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [resolvendoId, setResolvendoId] = useState<string | null>(null);
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);

  const {
    data: rascunho,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["rascunho", rascunhoId],
    queryFn: () => api.get<Rascunho>(`/entradas/rascunhos/${rascunhoId}`),
  });

  const confirmar = useMutation({
    mutationFn: () => api.post(`/entradas/rascunhos/${rascunhoId}/confirmar`, {}),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["rascunhos"] });
      void navigate({ to: "/app/estoque/entradas" });
    },
    onError: (err: Error) => setErroAcao(err.message),
  });

  const cancelar = useMutation({
    mutationFn: () => api.delete(`/entradas/rascunhos/${rascunhoId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["rascunhos"] });
      void navigate({ to: "/app/estoque/entradas" });
    },
    onError: (err: Error) =>
      setErroAcao(
        err instanceof ApiError && err.status === 409
          ? "Este rascunho já foi confirmado ou cancelado."
          : err.message
      ),
  });

  function abrirResolver(itemId: string) {
    setEditandoId(null);
    setResolvendoId((prev) => (prev === itemId ? null : itemId));
  }

  function abrirEditar(itemId: string) {
    setResolvendoId(null);
    setEditandoId((prev) => (prev === itemId ? null : itemId));
  }

  function handleItemResolved() {
    setResolvendoId(null);
    void refetch();
  }

  if (isLoading) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!rascunho) {
    return (
      <div className="p-8">
        <p className="text-sm text-[--color-error]">Rascunho não encontrado.</p>
        <Link
          to="/app/estoque/entradas"
          className="text-sm text-[--color-primary] hover:underline mt-2 block"
        >
          ← Voltar
        </Link>
      </div>
    );
  }

  const encerrado = rascunho.status !== "PENDENTE";
  const podeConfirmar = !encerrado && rascunho.pendentes === 0;

  return (
    <div className="p-8 space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-[--color-text-muted]">
        <Link to="/app/estoque" className="hover:text-[--color-text-primary]">
          Estoque
        </Link>
        <span>/</span>
        <Link to="/app/estoque/entradas" className="hover:text-[--color-text-primary]">
          Importar NF-e
        </Link>
        <span>/</span>
        <span className="text-[--color-text-primary]">Revisão</span>
      </div>

      {/* Cabeçalho NF-e */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-[--color-text-primary]">
            NF-e {rascunho.numero_nf ?? "s/nº"}
          </h1>
          {rascunho.chave_nfe && (
            <p className="text-xs font-mono text-[--color-text-muted] mt-0.5 break-all">
              {rascunho.chave_nfe}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {rascunho.status === "PENDENTE" && rascunho.pendentes > 0 && (
            <span className="text-sm text-[--color-warning] font-medium">
              {rascunho.pendentes} item{rascunho.pendentes !== 1 ? "s" : ""} pendente
              {rascunho.pendentes !== 1 ? "s" : ""}
            </span>
          )}
          {rascunho.status === "PENDENTE" && rascunho.pendentes === 0 && (
            <span className="text-sm text-[--color-success] font-medium">
              Todos os itens vinculados
            </span>
          )}
          <Badge
            variant={
              rascunho.status === "CONFIRMADA"
                ? "success"
                : rascunho.status === "CANCELADA"
                  ? "secondary"
                  : "warning"
            }
          >
            {rascunho.status === "CONFIRMADA"
              ? "Confirmada"
              : rascunho.status === "CANCELADA"
                ? "Cancelada"
                : "Pendente"}
          </Badge>
        </div>
      </div>

      {/* Resumo */}
      <Card>
        <CardContent className="pt-4">
          <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-3 text-sm">
            <div>
              <dt className="text-[--color-text-muted]">Emissão</dt>
              <dd className="text-[--color-text-primary]">{rascunho.data_emissao ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-[--color-text-muted]">Total</dt>
              <dd className="text-[--color-text-primary] font-medium">
                {fmtBrl(rascunho.valor_total)}
              </dd>
            </div>
            <div>
              <dt className="text-[--color-text-muted]">Itens</dt>
              <dd className="text-[--color-text-primary]">{rascunho.itens.length}</dd>
            </div>
            <div>
              <dt className="text-[--color-text-muted]">Importado em</dt>
              <dd className="text-[--color-text-primary]">
                {new Date(rascunho.criado_em).toLocaleDateString("pt-BR")}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Itens */}
      <Card>
        <CardHeader>
          <CardTitle>Itens da NF-e</CardTitle>
        </CardHeader>
        <CardContent className="px-0 pb-0">
          <div className="divide-y divide-[--color-border]">
            {rascunho.itens.map((item) => {
              const status = ITEM_STATUS_BADGE[item.status_item];
              const resolvendoEsteItem = resolvendoId === item.id;
              const editandoEsteItem = editandoId === item.id;
              const podeEditar = item.produto_id !== null && !encerrado;

              return (
                <div key={item.id} className="px-6 py-3">
                  <div className="flex items-start gap-4 flex-wrap sm:flex-nowrap">
                    {/* Descrição e código */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-[--color-text-primary] leading-snug">
                        {item.descricao_nfe}
                      </p>
                      <div className="flex gap-3 mt-0.5 flex-wrap">
                        <span className="text-xs font-mono text-[--color-text-muted]">
                          cProd: {item.codigo_fornecedor}
                        </span>
                        {item.codigo_ref && (
                          <span className="text-xs font-mono text-[--color-text-secondary]">
                            ref: {item.codigo_ref}
                          </span>
                        )}
                        {item.ean && (
                          <span className="text-xs font-mono text-[--color-text-muted]">
                            EAN: {item.ean}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Qtd + preço */}
                    <div className="text-right text-sm shrink-0">
                      <p className="text-[--color-text-primary]">
                        {fmtQtd(item.quantidade)} × {fmtBrl(item.preco_unitario)}
                      </p>
                      {(Number.parseFloat(item.icms) > 0 || Number.parseFloat(item.ipi) > 0) && (
                        <p className="text-xs text-[--color-text-muted]">
                          ICMS {item.icms}% · IPI {item.ipi}%
                        </p>
                      )}
                    </div>

                    {/* Status + ações */}
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant={status.variant}>{status.label}</Badge>
                      {item.status_item === "PENDENTE" && !encerrado && (
                        <Button
                          size="sm"
                          variant={resolvendoEsteItem ? "ghost" : "outline"}
                          onClick={() => abrirResolver(item.id)}
                        >
                          {resolvendoEsteItem ? "Fechar" : "Resolver"}
                        </Button>
                      )}
                      {podeEditar && (
                        <Button
                          size="sm"
                          variant={editandoEsteItem ? "ghost" : "outline"}
                          onClick={() => abrirEditar(item.id)}
                        >
                          {editandoEsteItem ? "Fechar" : "Editar"}
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Painel de resolução */}
                  {resolvendoEsteItem && (
                    <div className="mt-3 pt-3 border-t border-[--color-border]">
                      <ResolverItem
                        rascunhoId={rascunhoId}
                        item={item}
                        onDone={handleItemResolved}
                      />
                    </div>
                  )}

                  {/* Painel de edição do produto */}
                  {editandoEsteItem && item.produto_id && (
                    <div className="mt-3 pt-3 border-t border-[--color-border]">
                      <EditarProdutoPanel
                        produtoId={item.produto_id}
                        onDone={() => setEditandoId(null)}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Ações */}
      {!encerrado && (
        <div className="flex items-center gap-3 flex-wrap">
          <Button
            disabled={!podeConfirmar || confirmar.isPending}
            onClick={() => {
              setErroAcao(null);
              confirmar.mutate();
            }}
          >
            {confirmar.isPending ? "Confirmando..." : "Confirmar NF-e"}
          </Button>
          <Button
            variant="outline"
            disabled={cancelar.isPending}
            onClick={() => {
              setErroAcao(null);
              cancelar.mutate();
            }}
          >
            {cancelar.isPending ? "Cancelando..." : "Cancelar rascunho"}
          </Button>
          {!podeConfirmar && rascunho.pendentes > 0 && (
            <p className="text-sm text-[--color-text-muted]">
              Resolva todos os itens pendentes para confirmar.
            </p>
          )}
          {erroAcao && <p className="text-sm text-[--color-error]">{erroAcao}</p>}
        </div>
      )}

      {rascunho.status === "CONFIRMADA" && (
        <div className="rounded-lg bg-[--color-success]/10 border border-[--color-success]/30 p-4">
          <p className="text-sm text-[--color-success] font-medium">
            NF-e confirmada — estoque atualizado.
          </p>
          <Link
            to="/app/estoque"
            className="text-sm text-[--color-primary] hover:underline mt-1 block"
          >
            Ver estoque →
          </Link>
        </div>
      )}
    </div>
  );
}
