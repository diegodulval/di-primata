import { ApiError, api } from "@/lib/api";
import { Badge, Button, Card, CardContent, Field, Input, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";

export const Route = createFileRoute("/app/estoque/nfe-revisao/$rascunhoId")({
  component: NfeRevisaoPage,
});

// ─── Types ────────────────────────────────────────────────────────────────────

type StatusItem = "AUTO_VINCULADO" | "VINCULADO" | "NOVO" | "PENDENTE";
type StatusRascunho = "PENDENTE" | "CONFIRMADA" | "CANCELADA";

interface ItemRascunho {
  id: string;
  produto_id: string | null;
  codigo_produto: string | null;
  marca_produto: string | null;
  codigo_fornecedor: string;
  codigo_ref: string | null;
  ean: string | null;
  descricao_nfe: string;
  ncm: string | null;
  quantidade: string;
  preco_unitario: string;
  icms: string;
  ipi: string;
  cfop: string | null;
  cst: string | null;
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

interface FornecedorResponse {
  id: string;
  razao_social: string;
  nome_fantasia: string | null;
  cnpj: string | null;
  inscricao_estadual: string | null;
  telefone: string | null;
  email: string | null;
  contato: string | null;
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

function fmtQtd(v: string) {
  return Number.parseFloat(v).toLocaleString("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3,
  });
}

function fmtBrl(v: string | number | null) {
  if (v === null || v === undefined) return "—";
  const n = typeof v === "string" ? Number.parseFloat(v) : v;
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function calcVenda(preco: string, margem: string): number {
  const p = Number.parseFloat(preco) || 0;
  const m = Number.parseFloat(margem) || 0;
  return p * (1 + m / 100);
}

// ─── Marca Combobox ───────────────────────────────────────────────────────────

function MarcaCombobox({
  value,
  onChange,
  marcas,
  disabled,
}: {
  value: string;
  onChange: (marca: string) => void;
  marcas: string[];
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [filtro, setFiltro] = useState(value);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFiltro(value);
  }, [value]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setFiltro(value);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open, value]);

  const opcoes = marcas.filter((m) => m.toLowerCase().includes(filtro.toLowerCase()));
  const temExato = marcas.some((m) => m.toLowerCase() === filtro.toLowerCase());

  function selecionar(marca: string) {
    onChange(marca);
    setFiltro(marca);
    setOpen(false);
  }

  return (
    <div ref={ref} className="relative">
      <input
        type="text"
        value={filtro}
        disabled={disabled}
        onChange={(e) => { setFiltro(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        placeholder="Marca..."
        className="w-full min-w-[80px] rounded border border-[--color-border] bg-[--color-surface] px-2 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-[--color-primary] disabled:opacity-50"
      />
      {open && !disabled && (
        <div className="absolute z-50 mt-0.5 w-44 max-h-40 overflow-y-auto rounded-md border border-[--color-border] bg-[--color-surface] shadow-md">
          {opcoes.map((m) => (
            <button
              key={m}
              type="button"
              onMouseDown={() => selecionar(m)}
              className="w-full px-3 py-1.5 text-left text-xs hover:bg-[--color-background] transition-colors"
            >
              {m}
            </button>
          ))}
          {filtro.trim() && !temExato && (
            <button
              type="button"
              onMouseDown={() => selecionar(filtro.trim())}
              className="w-full px-3 py-1.5 text-left text-xs text-[--color-primary] hover:bg-[--color-background] transition-colors"
            >
              + Adicionar &ldquo;{filtro.trim()}&rdquo;
            </button>
          )}
          {opcoes.length === 0 && !filtro.trim() && (
            <p className="px-3 py-2 text-xs text-[--color-text-muted]">Nenhuma marca</p>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Step indicator ───────────────────────────────────────────────────────────

function StepIndicator({ passo }: { passo: "fornecedor" | "produtos" }) {
  const steps = [
    { label: "Importação", done: true, active: false },
    { label: "Fornecedor", done: passo === "produtos", active: passo === "fornecedor" },
    { label: "Produtos", done: false, active: passo === "produtos" },
  ];
  return (
    <div className="flex items-center justify-center mb-6">
      {steps.map((s, i) => (
        <div key={s.label} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                s.done
                  ? "bg-green-500 text-white"
                  : s.active
                    ? "bg-[--color-primary] text-[--color-primary-fg]"
                    : "bg-[--color-border] text-[--color-text-muted]"
              }`}
            >
              {s.done ? "✓" : i + 1}
            </div>
            <span
              className={`text-xs mt-1 whitespace-nowrap ${
                s.active
                  ? "font-semibold text-[--color-text-primary]"
                  : "text-[--color-text-muted]"
              }`}
            >
              {s.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div
              className={`h-1 w-20 mx-1 mb-4 rounded ${s.done ? "bg-green-500" : "bg-[--color-border]"}`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Editar produto inline ────────────────────────────────────────────────────

function EditarProdutoPanel({ produtoId, onDone }: { produtoId: string; onDone: () => void }) {
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

  if (isLoading) return <Skeleton className="h-24 w-full" />;
  if (!produto) return null;

  return (
    <div className="space-y-3 p-3 bg-[--color-background] rounded-md border border-[--color-border]">
      <p className="text-xs text-[--color-text-muted]">
        Produto: <span className="font-mono text-[--color-text-secondary]">{produto.codigo}</span>
        {" · "}estoque atual: {fmtQtd(produto.estoque_atual)}
      </p>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <Field label="Descrição">
            <Input value={descricao} onChange={(e) => setDescricao(e.target.value)} />
          </Field>
        </div>
        <Field label="Marca">
          <Input value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="—" />
        </Field>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Custo (R$)">
            <Input
              type="number"
              min="0"
              step="0.01"
              value={precoCusto}
              onChange={(e) => setPrecoCusto(e.target.value)}
            />
          </Field>
          <Field label="Venda (R$)">
            <Input
              type="number"
              min="0"
              step="0.01"
              value={precoVenda}
              onChange={(e) => setPrecoVenda(e.target.value)}
            />
          </Field>
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

// ─── Cód. Estoque inline (PENDENTE) ──────────────────────────────────────────

function CodigoEstoqueInput({
  rascunhoId,
  itemId,
  onVinculado,
}: {
  rascunhoId: string;
  itemId: string;
  onVinculado: () => void;
}) {
  const [busca, setBusca] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: produtos } = useQuery({
    queryKey: ["produtos-busca", busca],
    queryFn: () => api.get<ProdutoOpcao[]>(`/produtos?q=${encodeURIComponent(busca)}`),
    enabled: busca.length >= 1,
  });

  const vincular = useMutation({
    mutationFn: (produtoId: string) =>
      api.patch(`/entradas/rascunhos/${rascunhoId}/itens/${itemId}`, {
        acao: "vincular",
        produto_id: produtoId,
      }),
    onSuccess: onVinculado,
  });

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <input
        type="text"
        value={busca}
        onChange={(e) => { setBusca(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        placeholder="Buscar cód..."
        className="w-full min-w-[90px] rounded border border-amber-300 bg-amber-50 px-2 py-0.5 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-amber-500 placeholder:text-amber-400"
      />
      {open && (
        <div className="absolute z-50 mt-0.5 w-72 max-h-48 overflow-y-auto rounded-md border border-[--color-border] bg-[--color-surface] shadow-lg">
          {(produtos ?? []).map((p) => (
            <button
              key={p.id}
              type="button"
              onMouseDown={() => { vincular.mutate(p.id); setBusca(p.codigo); setOpen(false); }}
              className="w-full px-3 py-2 text-left text-xs hover:bg-[--color-background] transition-colors"
            >
              <span className="font-mono text-[--color-text-primary] mr-2">{p.codigo}</span>
              <span className="text-[--color-text-muted]">{p.descricao}</span>
            </button>
          ))}
          {busca.length >= 1 && (produtos?.length ?? 0) === 0 && (
            <p className="px-3 py-2 text-xs text-[--color-text-muted] italic">
              Nenhum produto — será criado ao confirmar.
            </p>
          )}
          {busca.length === 0 && (
            <p className="px-3 py-2 text-xs text-[--color-text-muted]">
              Digite código ou descrição. Em branco cria novo produto.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Passo 2 — Fornecedor ────────────────────────────────────────────────────

interface FornecedorForm {
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  inscricao_estadual: string;
  telefone: string;
  email: string;
}

function PassoFornecedor({
  rascunho,
  onAvancar,
  onVoltar,
}: {
  rascunho: Rascunho;
  onAvancar: () => void;
  onVoltar: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<FornecedorForm>({
    razao_social: "",
    nome_fantasia: "",
    cnpj: "",
    inscricao_estadual: "",
    telefone: "",
    email: "",
  });
  const [atualizado, setAtualizado] = useState(false);
  const [erroAtual, setErroAtual] = useState<string | null>(null);

  const { data: fornecedor, isLoading } = useQuery<FornecedorResponse>({
    queryKey: ["fornecedor", rascunho.fornecedor_id],
    queryFn: () => api.get<FornecedorResponse>(`/fornecedores/${rascunho.fornecedor_id}`),
    enabled: !!rascunho.fornecedor_id,
  });

  useEffect(() => {
    if (fornecedor) {
      setForm({
        razao_social: fornecedor.razao_social,
        nome_fantasia: fornecedor.nome_fantasia ?? "",
        cnpj: fornecedor.cnpj ?? "",
        inscricao_estadual: fornecedor.inscricao_estadual ?? "",
        telefone: fornecedor.telefone ?? "",
        email: fornecedor.email ?? "",
      });
    }
  }, [fornecedor]);

  const set = (field: keyof FornecedorForm) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setAtualizado(false);
  };

  const atualizar = useMutation({
    mutationFn: () =>
      api.patch(`/fornecedores/${rascunho.fornecedor_id}`, {
        razao_social: form.razao_social || undefined,
        nome_fantasia: form.nome_fantasia || null,
        inscricao_estadual: form.inscricao_estadual || null,
        telefone: form.telefone || null,
        email: form.email || null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fornecedor", rascunho.fornecedor_id] });
      setAtualizado(true);
      setErroAtual(null);
    },
    onError: (e: Error) => setErroAtual(e.message),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {!rascunho.fornecedor_id && (
        <p className="text-sm text-[--color-text-muted]">
          Nenhum fornecedor identificado nesta NF-e.
        </p>
      )}

      {rascunho.fornecedor_id && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Razão Social">
              <Input value={form.razao_social} onChange={set("razao_social")} />
            </Field>
            <Field label="Nome Fantasia">
              <Input value={form.nome_fantasia} onChange={set("nome_fantasia")} />
            </Field>
            <Field label="CNPJ">
              <Input value={form.cnpj} disabled className="opacity-60" />
            </Field>
            <Field label="Inscrição Estadual">
              <Input value={form.inscricao_estadual} onChange={set("inscricao_estadual")} />
            </Field>
            <Field label="Telefone Comercial">
              <Input value={form.telefone} onChange={set("telefone")} />
            </Field>
            <Field label="E-mail">
              <Input type="email" value={form.email} onChange={set("email")} />
            </Field>
          </div>

          {erroAtual && <p className="text-sm text-[--color-error]">{erroAtual}</p>}
          {atualizado && (
            <p className="text-sm text-green-600">Cadastro atualizado com sucesso.</p>
          )}
        </>
      )}

      <div className="flex items-center justify-between pt-2">
        <Button variant="destructive" onClick={onVoltar}>
          Voltar
        </Button>
        <div className="flex gap-2">
          {rascunho.fornecedor_id && (
            <Button
              variant="outline"
              disabled={atualizar.isPending}
              onClick={() => atualizar.mutate()}
            >
              {atualizar.isPending ? "Salvando..." : "Atualizar Cadastro"}
            </Button>
          )}
          <Button onClick={onAvancar}>Avançar</Button>
        </div>
      </div>
    </div>
  );
}

// ─── Passo 3 — Produtos ───────────────────────────────────────────────────────

const STATUS_BADGE: Record<StatusItem, { label: string; variant: "success" | "warning" | "secondary" | "default" }> = {
  AUTO_VINCULADO: { label: "Auto", variant: "success" },
  VINCULADO: { label: "Vinculado", variant: "success" },
  NOVO: { label: "Novo", variant: "success" },
  PENDENTE: { label: "Pendente", variant: "warning" },
};

function PassoProdutos({
  rascunho,
  onVoltar,
  onConfirmar,
  confirmando,
  erroConfirmar,
}: {
  rascunho: Rascunho;
  onVoltar: () => void;
  onConfirmar: () => void;
  confirmando: boolean;
  erroConfirmar: string | null;
}) {
  const queryClient = useQueryClient();
  const [busca, setBusca] = useState("");
  const [margemPadrao, setMargemPadrao] = useState("0");
  const [margemItens, setMargemItens] = useState<Record<string, string>>({});
  const [marcasItens, setMarcasItens] = useState<Record<string, string>>({});
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [selecionados, setSelecionados] = useState<Record<string, boolean>>({});
  const [autoCreando, setAutoCreando] = useState(false);

  const { data: marcas } = useQuery({
    queryKey: ["marcas"],
    queryFn: () => api.get<string[]>("/produtos/marcas"),
  });

  useEffect(() => {
    setMarcasItens((prev) => {
      const next = { ...prev };
      for (const item of rascunho.itens) {
        if (!(item.id in next)) {
          next[item.id] = item.marca_produto ?? "";
        }
      }
      return next;
    });
  }, [rascunho.itens]);

  const atualizarMarca = useMutation({
    mutationFn: ({ produtoId, marca }: { produtoId: string; marca: string }) =>
      api.patch(`/produtos/${produtoId}`, { marca: marca || null }),
  });

  const itens = rascunho.itens.filter((item) => {
    if (!busca) return true;
    const q = busca.toLowerCase();
    return (
      item.descricao_nfe.toLowerCase().includes(q) ||
      item.codigo_fornecedor.toLowerCase().includes(q) ||
      (item.codigo_ref ?? "").toLowerCase().includes(q) ||
      (item.ean ?? "").includes(q)
    );
  });

  function aplicarMargem() {
    const next: Record<string, string> = {};
    for (const item of rascunho.itens) {
      next[item.id] = margemPadrao;
    }
    setMargemItens(next);
  }

  function selecionarTodos() {
    const todos: Record<string, boolean> = {};
    for (const item of itens) {
      todos[item.id] = true;
    }
    setSelecionados(todos);
  }

  async function handleConcluir() {
    const pendentes = rascunho.itens.filter((i) => i.status_item === "PENDENTE");
    if (pendentes.length > 0) {
      setAutoCreando(true);
      try {
        for (const item of pendentes) {
          await api.patch(`/entradas/rascunhos/${rascunho.id}/itens/${item.id}`, {
            acao: "criar_novo",
            marca: marcasItens[item.id] || undefined,
          });
        }
      } catch {
        setAutoCreando(false);
        return;
      }
      setAutoCreando(false);
    }
    onConfirmar();
  }

  const encerrado = rascunho.status !== "PENDENTE";

  return (
    <div className="space-y-4">
      {/* Barra de ferramentas */}
      <div className="flex items-center gap-3 flex-wrap">
        <input
          type="search"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Pesquisa por Código / Descrição / Ref. Fab / Código de Barras"
          className="flex-1 min-w-48 rounded border border-[--color-border] bg-[--color-surface] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <div className="flex items-center gap-2 ml-auto shrink-0">
          <span className="text-xs text-[--color-text-muted]">Margem Padrão:</span>
          <input
            type="number"
            min="0"
            step="0.01"
            value={margemPadrao}
            onChange={(e) => setMargemPadrao(e.target.value)}
            className="w-20 rounded border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm text-right focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
          <span className="text-xs text-[--color-text-muted]">%</span>
          <Button size="sm" variant="outline" onClick={aplicarMargem}>
            Aplicar Margem
          </Button>
        </div>
      </div>

      {/* Selecionar todos */}
      <button
        type="button"
        onClick={selecionarTodos}
        className="text-xs text-[--color-primary] hover:underline"
      >
        Selecionar todos ({itens.length})
      </button>

      {/* Tabela */}
      <div className="overflow-x-auto rounded-lg border border-[--color-border]">
        <table className="w-full text-sm min-w-[900px]">
          <thead>
            <tr className="bg-[--color-surface] border-b border-[--color-border] text-left text-xs font-medium text-[--color-text-muted]">
              <th className="px-2 py-2 w-8" />
              <th className="px-3 py-2">Ordem</th>
              <th className="px-3 py-2">Cód. Estoque</th>
              <th className="px-3 py-2">Marca</th>
              <th className="px-3 py-2">Cód. Fornecedor</th>
              <th className="px-3 py-2">Descrição</th>
              <th className="px-3 py-2 text-right">Qtd.</th>
              <th className="px-3 py-2 text-right">R$ Compra</th>
              <th className="px-3 py-2 text-right">Margem %</th>
              <th className="px-3 py-2 text-right">R$ Venda</th>
              <th className="px-3 py-2">NCM</th>
              <th className="px-3 py-2">CST</th>
              <th className="px-3 py-2">CFOP</th>
              <th className="px-3 py-2">EAN</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[--color-border]">
            {itens.map((item, idx) => {
              const margem = margemItens[item.id] ?? "0";
              const precoVenda = calcVenda(item.preco_unitario, margem);
              const editandoEste = editandoId === item.id;
              const status = STATUS_BADGE[item.status_item];

              return (
                <>
                  <tr
                    key={item.id}
                    className={`bg-[--color-surface] hover:bg-[--color-background] transition-colors ${
                      item.status_item === "PENDENTE" ? "border-l-2 border-l-amber-400" : ""
                    }`}
                  >
                    <td className="px-2 py-2.5 text-center">
                      <input
                        type="checkbox"
                        checked={!!selecionados[item.id]}
                        onChange={(e) =>
                          setSelecionados((prev) => ({ ...prev, [item.id]: e.target.checked }))
                        }
                        className="rounded"
                      />
                    </td>
                    <td className="px-3 py-2.5 text-[--color-text-muted] text-xs">{idx + 1}</td>
                    <td className="px-3 py-2">
                      {item.status_item === "PENDENTE" && !encerrado ? (
                        <CodigoEstoqueInput
                          rascunhoId={rascunho.id}
                          itemId={item.id}
                          onVinculado={() => {
                            void queryClient.invalidateQueries({ queryKey: ["rascunho", rascunho.id] });
                          }}
                        />
                      ) : (
                        <span className="font-mono text-xs text-[--color-text-primary] font-medium">
                          {item.codigo_produto ?? "—"}
                        </span>
                      )}
                    </td>
                    <td className="px-2 py-1.5">
                      <MarcaCombobox
                        value={marcasItens[item.id] ?? ""}
                        disabled={encerrado}
                        marcas={marcas ?? []}
                        onChange={(marca) => {
                          setMarcasItens((prev) => ({ ...prev, [item.id]: marca }));
                          if (item.produto_id && !encerrado) {
                            atualizarMarca.mutate({ produtoId: item.produto_id, marca });
                          }
                        }}
                      />
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-[--color-text-secondary]">
                      {item.codigo_fornecedor}
                    </td>
                    <td className="px-3 py-2.5 max-w-56">
                      <p className="text-[--color-text-primary] truncate" title={item.descricao_nfe}>
                        {item.descricao_nfe}
                      </p>
                      {item.codigo_ref && (
                        <p className="text-xs font-mono text-[--color-text-muted]">
                          ref: {item.codigo_ref}
                        </p>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-right text-[--color-text-secondary]">
                      {fmtQtd(item.quantidade)}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-[--color-text-primary]">
                      {fmtBrl(item.preco_unitario)}
                    </td>
                    <td className="px-3 py-2.5">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={margem}
                        onChange={(e) =>
                          setMargemItens((prev) => ({ ...prev, [item.id]: e.target.value }))
                        }
                        className="w-16 rounded border border-[--color-border] bg-[--color-surface] px-2 py-0.5 text-xs text-right focus:outline-none focus:ring-1 focus:ring-[--color-primary]"
                      />
                      <span className="text-xs text-[--color-text-muted] ml-0.5">%</span>
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-[--color-text-primary]">
                      {fmtBrl(precoVenda)}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-[--color-text-muted]">
                      {item.ncm ?? "—"}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-[--color-text-muted]">
                      {item.cst ?? "—"}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-[--color-text-muted]">
                      {item.cfop ?? "—"}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-[--color-text-muted]">
                      {item.ean ?? "—"}
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <Badge variant={status.variant}>{status.label}</Badge>
                        {item.produto_id && !encerrado && (
                          <button
                            type="button"
                            onClick={() => setEditandoId((prev) => (prev === item.id ? null : item.id))}
                            className="text-xs text-[--color-text-muted] hover:underline"
                          >
                            {editandoEste ? "Fechar" : "Editar"}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {editandoEste && item.produto_id && (
                    <tr key={`${item.id}-editar`}>
                      <td colSpan={15} className="px-6 py-3">
                        <EditarProdutoPanel
                          produtoId={item.produto_id}
                          onDone={() => setEditandoId(null)}
                        />
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>

      {rascunho.pendentes > 0 && !encerrado && (
        <p className="text-sm text-amber-600">
          {rascunho.pendentes} item{rascunho.pendentes !== 1 ? "s" : ""} sem vínculo — será
          {rascunho.pendentes !== 1 ? "ão" : ""} criado{rascunho.pendentes !== 1 ? "s" : ""} como novo
          {rascunho.pendentes !== 1 ? "s produtos" : " produto"} ao confirmar.
        </p>
      )}

      {erroConfirmar && <p className="text-sm text-[--color-error]">{erroConfirmar}</p>}

      <div className="flex items-center justify-between pt-2">
        <Button variant="destructive" onClick={onVoltar} disabled={encerrado}>
          Voltar
        </Button>
        {!encerrado && (
          <Button disabled={confirmando || autoCreando} onClick={() => void handleConcluir()}>
            {autoCreando ? "Preparando..." : confirmando ? "Confirmando..." : "Concluir"}
          </Button>
        )}
        {encerrado && (
          <Badge variant={rascunho.status === "CONFIRMADA" ? "success" : "secondary"}>
            {rascunho.status === "CONFIRMADA" ? "Confirmada" : "Cancelada"}
          </Badge>
        )}
      </div>
    </div>
  );
}

// ─── Página principal ─────────────────────────────────────────────────────────

function NfeRevisaoPage() {
  const { rascunhoId } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [passo, setPasso] = useState<"fornecedor" | "produtos">("fornecedor");
  const [erroConfirmar, setErroConfirmar] = useState<string | null>(null);

  const { data: rascunho, isLoading } = useQuery({
    queryKey: ["rascunho", rascunhoId],
    queryFn: () => api.get<Rascunho>(`/entradas/rascunhos/${rascunhoId}`),
  });

  const cancelar = useMutation({
    mutationFn: () => api.delete(`/entradas/rascunhos/${rascunhoId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["rascunhos"] });
      void navigate({ to: "/app/estoque/entradas" });
    },
    onError: (err: Error) =>
      setErroConfirmar(
        err instanceof ApiError && err.status === 409
          ? "Este rascunho já foi confirmado ou cancelado."
          : err.message,
      ),
  });

  const confirmar = useMutation({
    mutationFn: () =>
      api.post<{ id: string }>(`/entradas/rascunhos/${rascunhoId}/confirmar`, {}),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["rascunhos"] });
      void navigate({
        to: "/app/estoque/entrada/$entradaId",
        params: { entradaId: data.id },
      });
    },
    onError: (err: Error) => setErroConfirmar(err.message),
  });

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

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-[--color-text-muted]">
        <Link to="/app/estoque/entradas" className="hover:text-[--color-text-primary]">
          ← Importar NF-e
        </Link>
        <span>/</span>
        <span className="text-[--color-text-primary]">
          NF-e {rascunho.numero_nf ?? "s/nº"}
        </span>
      </div>

      <Card>
        <CardContent className="pt-6">
          {/* Título + info NF-e */}
          <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
            <div>
              <h1 className="text-lg font-semibold text-[--color-text-primary]">
                Importação de XML de Compra
              </h1>
              {rascunho.chave_nfe && (
                <p className="text-xs font-mono text-[--color-text-muted] mt-0.5 break-all">
                  {rascunho.chave_nfe}
                </p>
              )}
            </div>
            <dl className="flex gap-6 text-sm">
              <div>
                <dt className="text-xs text-[--color-text-muted]">Emissão</dt>
                <dd className="text-[--color-text-primary]">{rascunho.data_emissao ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs text-[--color-text-muted]">Total</dt>
                <dd className="font-medium text-[--color-text-primary]">
                  {fmtBrl(rascunho.valor_total)}
                </dd>
              </div>
            </dl>
          </div>

          {/* Step indicator */}
          <StepIndicator passo={passo} />

          {/* Cancelar (link discreto) */}
          {rascunho.status === "PENDENTE" && (
            <div className="flex justify-end mb-4">
              <button
                type="button"
                onClick={() => cancelar.mutate()}
                disabled={cancelar.isPending}
                className="text-xs text-[--color-text-muted] hover:text-[--color-error] transition-colors"
              >
                {cancelar.isPending ? "Cancelando..." : "Cancelar importação"}
              </button>
            </div>
          )}

          {/* Passo ativo */}
          {passo === "fornecedor" ? (
            <PassoFornecedor
              rascunho={rascunho}
              onAvancar={() => setPasso("produtos")}
              onVoltar={() => navigate({ to: "/app/estoque/entradas" })}
            />
          ) : (
            <PassoProdutos
              rascunho={rascunho}
              onVoltar={() => setPasso("fornecedor")}
              onConfirmar={() => { setErroConfirmar(null); confirmar.mutate(); }}
              confirmando={confirmar.isPending}
              erroConfirmar={erroConfirmar}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
