import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useEffect, useRef, useState } from "react";

const INPUT_CLS =
  "w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]";

interface ImportacaoResult {
  criados: number;
  atualizados: number;
  ignorados: number;
  erros: string[];
}

interface Marca {
  id: string;
  nome: string;
  ativo: boolean;
}

interface Produto {
  id: string;
  codigo: string;
  descricao: string;
  marca_id: string | null;
  localizacao: string | null;
  ean: string | null;
  ref_fabricante: string | null;
  unidade_medida: string;
  preco_custo: string;
  preco_venda: string;
  estoque_atual: string;
  estoque_minimo: string;
  estoque_maximo: string;
  peso_liquido: string;
  peso_bruto: string;
  origem_mercadoria: string;
  observacoes: string | null;
  ativo: boolean;
}

interface ProdutosPaginados {
  items: Produto[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const PAGE_SIZE = 50;

// ─── MarcaSelectCombobox ──────────────────────────────────────────────────────

function MarcaSelectCombobox({
  value,
  onChange,
  marcas,
}: {
  value: string | null;
  onChange: (id: string | null) => void;
  marcas: Marca[];
}) {
  const queryClient = useQueryClient();
  const selecionada = marcas.find((m) => m.id === value) ?? null;
  const [open, setOpen] = useState(false);
  const [filtro, setFiltro] = useState(selecionada?.nome ?? "");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFiltro(selecionada?.nome ?? "");
  }, [selecionada?.nome]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setFiltro(selecionada?.nome ?? "");
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open, selecionada?.nome]);

  const termo = filtro.trim();
  const opcoes = marcas.filter((m) => m.nome.toLowerCase().includes(filtro.toLowerCase()));
  const temExato = marcas.some((m) => m.nome.toLowerCase() === termo.toLowerCase());

  const cadastrar = useMutation({
    mutationFn: (nome: string) => api.post<Marca>("/marcas", { nome }),
    onSuccess: async (nova) => {
      await queryClient.invalidateQueries({ queryKey: ["marcas"] });
      onChange(nova.id);
      setFiltro(nova.nome);
      setOpen(false);
    },
  });

  function selecionar(m: Marca) {
    onChange(m.id);
    setFiltro(m.nome);
    setOpen(false);
  }

  function limpar() {
    onChange(null);
    setFiltro("");
    setOpen(false);
  }

  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <input
          type="text"
          value={filtro}
          onChange={(e) => {
            setFiltro(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Buscar marca..."
          className={INPUT_CLS}
        />
        {value && (
          <button
            type="button"
            onMouseDown={limpar}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-[--color-text-muted] hover:text-[--color-text-primary] px-1 text-xs"
          >
            ✕
          </button>
        )}
      </div>
      {open && (
        <div className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-md border border-[--color-border] bg-[var(--color-surface)] shadow-lg">
          {opcoes.map((m) => (
            <button
              key={m.id}
              type="button"
              onMouseDown={() => selecionar(m)}
              className={`w-full px-3 py-2 text-left text-sm hover:bg-[var(--color-background)] transition-colors ${m.id === value ? "font-medium text-[--color-primary]" : "text-[--color-text-primary]"}`}
            >
              {m.nome}
            </button>
          ))}
          {termo && !temExato && (
            <button
              type="button"
              disabled={cadastrar.isPending}
              onMouseDown={() => cadastrar.mutate(termo)}
              className="w-full px-3 py-2 text-left text-sm text-[--color-primary] hover:bg-[var(--color-background)] transition-colors border-t border-[--color-border] disabled:opacity-50"
            >
              {cadastrar.isPending ? "Cadastrando..." : `+ Cadastrar "${termo}"`}
            </button>
          )}
          {opcoes.length === 0 && !termo && (
            <p className="px-3 py-2 text-sm text-[--color-text-muted]">
              Nenhuma marca cadastrada
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ─── NovoProdutoForm ──────────────────────────────────────────────────────────

function NovoProdutoForm({ onClose, marcas }: { onClose: () => void; marcas: Marca[] }) {
  const queryClient = useQueryClient();
  const [codigo, setCodigo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [marcaId, setMarcaId] = useState<string | null>(null);
  const [precoCusto, setPrecoCusto] = useState("");
  const [precoVenda, setPrecoVenda] = useState("");
  const [error, setError] = useState<string | null>(null);

  const criar = useMutation({
    mutationFn: () =>
      api.post("/produtos", {
        codigo,
        descricao,
        marca_id: marcaId,
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
    <Card className="mb-6 bg-[var(--color-surface)]">
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
                className={INPUT_CLS}
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-[--color-text-primary]">Marca</label>
              <MarcaSelectCombobox value={marcaId} onChange={setMarcaId} marcas={marcas} />
            </div>
            <div className="space-y-1 sm:col-span-2">
              <label
                htmlFor="np-desc"
                className="text-sm font-medium text-[--color-text-primary]"
              >
                Descrição *
              </label>
              <input
                id="np-desc"
                required
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                className={INPUT_CLS}
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
                className={INPUT_CLS}
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
                className={INPUT_CLS}
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

const ORIGENS = [
  { value: "0", label: "0 – Nacional" },
  { value: "1", label: "1 – Estrangeira (importação direta)" },
  { value: "2", label: "2 – Estrangeira (adquirida no mercado interno)" },
  { value: "3", label: "3 – Nacional, c/ conteúdo importado > 40%" },
  { value: "4", label: "4 – Nacional, produção básica" },
  { value: "5", label: "5 – Nacional, c/ conteúdo importado ≤ 40%" },
  { value: "6", label: "6 – Estrangeira (importação direta) s/ similar nacional" },
  { value: "7", label: "7 – Estrangeira (mercado interno) s/ similar nacional" },
  { value: "8", label: "8 – Nacional, c/ conteúdo importado > 70%" },
];

// ─── EditarProdutoModal ───────────────────────────────────────────────────────

function EditarProdutoModal({
  produto,
  onClose,
  marcas,
}: {
  produto: Produto;
  onClose: () => void;
  marcas: Marca[];
}) {
  const queryClient = useQueryClient();
  const [descricao, setDescricao] = useState(produto.descricao);
  const [marcaId, setMarcaId] = useState<string | null>(produto.marca_id ?? null);
  const [localizacao, setLocalizacao] = useState(produto.localizacao ?? "");
  const [ean, setEan] = useState(produto.ean ?? "");
  const [refFabricante, setRefFabricante] = useState(produto.ref_fabricante ?? "");
  const [unidadeMedida, setUnidadeMedida] = useState(produto.unidade_medida);
  const [precoCusto, setPrecoCusto] = useState(produto.preco_custo);
  const [precoVenda, setPrecoVenda] = useState(produto.preco_venda);
  const [estoqueMinimo, setEstoqueMinimo] = useState(produto.estoque_minimo);
  const [estoqueMaximo, setEstoqueMaximo] = useState(produto.estoque_maximo);
  const [pesoLiquido, setPesoLiquido] = useState(produto.peso_liquido);
  const [pesoBruto, setPesoBruto] = useState(produto.peso_bruto);
  const [origem, setOrigem] = useState(produto.origem_mercadoria);
  const [observacoes, setObservacoes] = useState(produto.observacoes ?? "");
  const [ativo, setAtivo] = useState(produto.ativo);
  const [error, setError] = useState<string | null>(null);

  const salvar = useMutation({
    mutationFn: () =>
      api.patch(`/produtos/${produto.id}`, {
        descricao,
        marca_id: marcaId,
        localizacao: localizacao || null,
        ean: ean || null,
        ref_fabricante: refFabricante || null,
        unidade_medida: unidadeMedida,
        preco_custo: Number(precoCusto),
        preco_venda: Number(precoVenda),
        estoque_minimo: Number(estoqueMinimo),
        estoque_maximo: Number(estoqueMaximo),
        peso_liquido: Number(pesoLiquido),
        peso_bruto: Number(pesoBruto),
        origem_mercadoria: origem,
        observacoes: observacoes || null,
        ativo,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["produtos"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-lg bg-[var(--color-surface)] shadow-xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between border-b border-[--color-border] px-6 py-4 shrink-0">
          <h2 className="text-base font-semibold text-[--color-text-primary]">
            Editar produto — <span className="font-mono text-sm">{produto.codigo}</span>
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-[--color-text-muted] hover:text-[--color-text-primary]"
          >
            ✕
          </button>
        </div>
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            salvar.mutate();
          }}
          className="px-6 py-4 space-y-4 overflow-y-auto"
        >
          {/* Dados básicos */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted]">
              Dados do produto
            </p>
            <div className="space-y-1">
              <label className="text-sm font-medium text-[--color-text-primary]">Descrição *</label>
              <input
                required
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                className={INPUT_CLS}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Marca</label>
                <MarcaSelectCombobox value={marcaId} onChange={setMarcaId} marcas={marcas} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Unidade</label>
                <select
                  value={unidadeMedida}
                  onChange={(e) => setUnidadeMedida(e.target.value)}
                  className={INPUT_CLS}
                >
                  {["UN", "PC", "KG", "LT", "MT", "CX", "PR", "JG"].map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Ref. Fabricante
                </label>
                <input
                  value={refFabricante}
                  onChange={(e) => setRefFabricante(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Localização
                </label>
                <input
                  value={localizacao}
                  onChange={(e) => setLocalizacao(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">EAN</label>
                <input
                  value={ean}
                  onChange={(e) => setEan(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-[--color-text-primary]">Observações</label>
              <textarea
                rows={2}
                value={observacoes}
                onChange={(e) => setObservacoes(e.target.value)}
                className={INPUT_CLS}
              />
            </div>
          </div>

          {/* Preços e estoque */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted]">
              Preços e estoque
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Preço de custo (R$)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={precoCusto}
                  onChange={(e) => setPrecoCusto(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Preço de venda (R$)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={precoVenda}
                  onChange={(e) => setPrecoVenda(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Estoque mínimo
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  value={estoqueMinimo}
                  onChange={(e) => setEstoqueMinimo(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Estoque máximo
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  value={estoqueMaximo}
                  onChange={(e) => setEstoqueMaximo(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
            </div>
          </div>

          {/* Fiscal / NF-e */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted]">
              Fiscal / NF-e
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Peso líquido (kg)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  value={pesoLiquido}
                  onChange={(e) => setPesoLiquido(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Peso bruto (kg)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  value={pesoBruto}
                  onChange={(e) => setPesoBruto(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
              <div className="space-y-1 col-span-2">
                <label className="text-sm font-medium text-[--color-text-primary]">
                  Origem da mercadoria
                </label>
                <select
                  value={origem}
                  onChange={(e) => setOrigem(e.target.value)}
                  className={INPUT_CLS}
                >
                  {ORIGENS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-[--color-text-primary] cursor-pointer">
            <input
              type="checkbox"
              checked={ativo}
              onChange={(e) => setAtivo(e.target.checked)}
              className="rounded"
            />
            Ativo
          </label>

          {error && <p className="text-sm text-[--color-error]">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={salvar.isPending}>
              {salvar.isPending ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── EstoquePage ──────────────────────────────────────────────────────────────

export const Route = createFileRoute("/app/estoque/")({
  component: EstoquePage,
});

function EstoquePage() {
  const [q, setQ] = useState("");
  const [qInput, setQInput] = useState("");
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Produto | null>(null);
  const [importResult, setImportResult] = useState<ImportacaoResult | null>(null);
  const xlsxInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: marcasData } = useQuery({
    queryKey: ["marcas"],
    queryFn: () => api.get<{ items: Marca[] }>("/marcas?ativo=true&page_size=1000"),
    staleTime: 60_000,
  });
  const marcas = marcasData?.items ?? [];

  const marcasMap = Object.fromEntries(marcas.map((m) => [m.id, m.nome]));

  function pesquisar() {
    setQ(qInput);
    setPage(1);
  }

  const { data, isLoading } = useQuery({
    queryKey: ["produtos", q, page],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
      });
      if (q) params.set("q", q);
      return api.get<ProdutosPaginados>(`/produtos?${params.toString()}`);
    },
    placeholderData: (prev) => prev,
  });

  const produtos = data?.items ?? [];
  const totalPages = data?.pages ?? 1;
  const total = data?.total ?? 0;

  const importarXlsx = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("arquivo", file);
      return api.postForm<ImportacaoResult>("/produtos/importar", form);
    },
    onSuccess: (res) => {
      setImportResult(res);
      void queryClient.invalidateQueries({ queryKey: ["produtos"] });
    },
    onError: (err: Error) =>
      setImportResult({ criados: 0, atualizados: 0, ignorados: 0, erros: [err.message] }),
  });

  function handleImportarXlsx(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportResult(null);
    importarXlsx.mutate(file);
    e.target.value = "";
  }

  return (
    <>
      {editando && (
        <EditarProdutoModal
          produto={editando}
          onClose={() => setEditando(null)}
          marcas={marcas}
        />
      )}
      <div className="p-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-[--color-text-primary]">Listagem de Produtos</h1>
          <div className="flex gap-2">
            <input
              ref={xlsxInputRef}
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={handleImportarXlsx}
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => xlsxInputRef.current?.click()}
              disabled={importarXlsx.isPending}
            >
              {importarXlsx.isPending ? "Importando..." : "↑ Importar XLSX"}
            </Button>
            <Button size="sm" onClick={() => setShowForm((v) => !v)}>
              {showForm ? "Cancelar" : "+ Novo produto"}
            </Button>
          </div>
        </div>

        {importResult && (
          <div
            className={`mb-4 rounded-md border px-4 py-3 text-sm ${importResult.erros.length > 0 ? "border-[--color-error] bg-[--color-error]/10" : "border-[--color-success] bg-[--color-success]/10"}`}
          >
            <p className="font-medium mb-1">
              Importação concluída — {importResult.criados} criados, {importResult.atualizados}{" "}
              atualizados, {importResult.ignorados} ignorados
            </p>
            {importResult.erros.length > 0 && (
              <ul className="list-disc list-inside text-[--color-error] space-y-0.5 mt-1">
                {importResult.erros.slice(0, 10).map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
                {importResult.erros.length > 10 && (
                  <li>…e mais {importResult.erros.length - 10} erros</li>
                )}
              </ul>
            )}
          </div>
        )}

        {showForm && <NovoProdutoForm onClose={() => setShowForm(false)} marcas={marcas} />}

        <div className="mb-4 flex gap-2 items-center">
          <input
            type="search"
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && pesquisar()}
            placeholder="Buscar por código ou descrição..."
            className="w-full max-w-sm rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
          <Button size="sm" variant="outline" onClick={pesquisar}>
            Buscar
          </Button>
          {total > 0 && (
            <span className="text-sm text-[--color-text-muted] ml-2">
              {total.toLocaleString("pt-BR")} produtos
            </span>
          )}
        </div>

        <Card>
          <CardContent className="pt-4">
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : produtos.length === 0 ? (
              <p className="text-sm text-[--color-text-muted] py-4 text-center">
                Nenhum produto encontrado.
              </p>
            ) : (
              <>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[var(--color-surface)] border-b border-[--color-border] text-left text-[--color-text-muted]">
                      <th className="pb-2 pr-4 font-medium">Código</th>
                      <th className="pb-2 pr-4 font-medium hidden lg:table-cell">Ref. Fabricante</th>
                      <th className="pb-2 pr-4 font-medium">Descrição</th>
                      <th className="pb-2 pr-4 font-medium hidden sm:table-cell">Marca</th>
                      <th className="pb-2 pr-4 font-medium text-right">Estoque</th>
                      <th className="pb-2 pr-4 font-medium text-right hidden md:table-cell">
                        Venda (R$)
                      </th>
                      <th className="pb-2 font-medium text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[--color-border]">
                    {produtos.map((p) => {
                      const atual = Number.parseFloat(p.estoque_atual);
                      const minimo = Number.parseFloat(p.estoque_minimo);
                      const baixo = minimo > 0 && atual <= minimo;

                      return (
                        <tr key={p.id} className={`bg-[var(--color-surface)] hover:bg-[var(--color-background)] transition-colors ${!p.ativo ? "opacity-50" : ""}`}>
                          <td className="py-3 pr-4 font-mono text-xs text-[--color-text-secondary]">
                            {p.codigo}
                          </td>
                          <td className="py-3 pr-4 font-mono text-xs text-[--color-text-secondary] hidden lg:table-cell">
                            {p.ref_fabricante ?? "—"}
                          </td>
                          <td className="py-3 pr-4 text-[--color-text-primary]">
                            {p.descricao}
                            {!p.ativo && (
                              <Badge variant="warning" className="ml-2 text-xs">
                                Inativo
                              </Badge>
                            )}
                          </td>
                          <td className="py-3 pr-4 text-[--color-text-secondary] hidden sm:table-cell">
                            {p.marca_id ? (marcasMap[p.marca_id] ?? "—") : "—"}
                          </td>
                          <td className="py-3 pr-4 text-right">
                            <span
                              className={
                                baixo
                                  ? "text-[--color-error] font-medium"
                                  : "text-[--color-text-primary]"
                              }
                            >
                              {Number.isInteger(atual) ? atual : atual.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}
                            </span>
                            {baixo && (
                              <Badge variant="error" className="ml-2 text-xs">
                                Baixo
                              </Badge>
                            )}
                          </td>
                          <td className="py-3 pr-4 text-right text-[--color-text-secondary] hidden md:table-cell">
                            {Number.parseFloat(p.preco_venda).toLocaleString("pt-BR", {
                              style: "currency",
                              currency: "BRL",
                            })}
                          </td>
                          <td className="py-3 text-right">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditando(p)}
                            >
                              Editar
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-4 border-t border-[--color-border] mt-2">
                    <span className="text-sm text-[--color-text-muted]">
                      Página {page} de {totalPages}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={page <= 1}
                        onClick={() => setPage((p) => p - 1)}
                      >
                        ← Anterior
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={page >= totalPages}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        Próxima →
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
