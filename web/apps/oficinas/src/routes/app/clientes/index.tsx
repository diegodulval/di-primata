import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";

// ─── Novo cliente (form inline) ────────────────────────────────────────────────

function NovoClienteForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState("");
  const [tipoPessoa, setTipoPessoa] = useState("Fisica");
  const [cpfCnpj, setCpfCnpj] = useState("");
  const [telefone, setTelefone] = useState("");
  const [celular, setCelular] = useState("");
  const [email, setEmail] = useState("");
  const [cidade, setCidade] = useState("");
  const [uf, setUf] = useState("");
  const [error, setError] = useState<string | null>(null);

  const criar = useMutation({
    mutationFn: () =>
      api.post("/clientes", {
        nome, tipo_pessoa: tipoPessoa,
        cpf_cnpj: cpfCnpj || null,
        telefone: telefone || null,
        celular: celular || null,
        email: email || null,
        cidade: cidade || null,
        uf: uf || null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["clientes"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div className="mb-6 rounded-lg border border-[--color-border] bg-[--color-surface] p-4">
      <h2 className="text-sm font-semibold text-[--color-text-primary] mb-3">Novo cliente</h2>
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); criar.mutate(); }} className="space-y-3">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div className="col-span-2 space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">Nome *</label>
            <input required value={nome} onChange={(e) => setNome(e.target.value)} className={INPUT_CLS} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">Tipo</label>
            <select value={tipoPessoa} onChange={(e) => setTipoPessoa(e.target.value)} className={INPUT_CLS}>
              <option value="Fisica">Física</option>
              <option value="Juridica">Jurídica</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">CPF/CNPJ</label>
            <input value={cpfCnpj} onChange={(e) => setCpfCnpj(e.target.value)} className={INPUT_CLS} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">Telefone</label>
            <input value={telefone} onChange={(e) => setTelefone(e.target.value)} className={INPUT_CLS} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">Celular</label>
            <input value={celular} onChange={(e) => setCelular(e.target.value)} className={INPUT_CLS} />
          </div>
          <div className="col-span-2 space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">E-mail</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={INPUT_CLS} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">Cidade</label>
            <input value={cidade} onChange={(e) => setCidade(e.target.value)} className={INPUT_CLS} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-[--color-text-primary]">UF</label>
            <input maxLength={2} value={uf} onChange={(e) => setUf(e.target.value.toUpperCase())} className={INPUT_CLS} />
          </div>
        </div>
        {error && <p className="text-sm text-[--color-error]">{error}</p>}
        <div className="flex gap-2 justify-end">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
          <Button type="submit" size="sm" disabled={criar.isPending}>
            {criar.isPending ? "Salvando..." : "Salvar"}
          </Button>
        </div>
      </form>
    </div>
  );
}
import { type FormEvent, useRef, useState } from "react";

export const Route = createFileRoute("/app/clientes/")({
  component: ClientesPage,
});

const INPUT_CLS =
  "w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]";

const PAGE_SIZE = 20;

interface Cliente {
  id: string;
  nome: string;
  tipo_pessoa: string | null;
  cpf_cnpj: string | null;
  rg: string | null;
  apelido: string | null;
  data_nascimento: string | null;
  sexo: string | null;
  telefone: string | null;
  celular: string | null;
  email: string | null;
  cep: string | null;
  endereco: string | null;
  cidade: string | null;
  uf: string | null;
  inscricao_estadual: string | null;
  consumidor_final: boolean;
  indicador_ie: string;
  observacoes: string | null;
  ativo: boolean;
}

interface ClientesPaginados {
  items: Cliente[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface ImportacaoResult {
  criados: number;
  atualizados: number;
  ignorados: number;
  erros: string[];
}

interface ImportacaoVeiculosResult {
  match_cpf: number;
  match_telefone: number;
  match_nome: number;
  clientes_nao_encontrados: number;
  clientes_enriquecidos: number;
  veiculos_upserted: number;
  vinculos_criados: number;
  placas_ignoradas: number;
  erros: string[];
}

function whatsappUrl(tel: string): string {
  const digits = tel.replace(/\D/g, "");
  const num = digits.startsWith("55") ? digits : `55${digits}`;
  return `https://wa.me/${num}`;
}

// ─── Editar cliente ────────────────────────────────────────────────────────────

function EditarClienteModal({ cliente, onClose }: { cliente: Cliente; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState(cliente.nome);
  const [tipoPessoa, setTipoPessoa] = useState(cliente.tipo_pessoa ?? "Fisica");
  const [cpfCnpj, setCpfCnpj] = useState(cliente.cpf_cnpj ?? "");
  const [rg, setRg] = useState(cliente.rg ?? "");
  const [apelido, setApelido] = useState(cliente.apelido ?? "");
  const [telefone, setTelefone] = useState(cliente.telefone ?? "");
  const [celular, setCelular] = useState(cliente.celular ?? "");
  const [email, setEmail] = useState(cliente.email ?? "");
  const [cep, setCep] = useState(cliente.cep ?? "");
  const [endereco, setEndereco] = useState(cliente.endereco ?? "");
  const [cidade, setCidade] = useState(cliente.cidade ?? "");
  const [uf, setUf] = useState(cliente.uf ?? "");
  const [ie, setIe] = useState(cliente.inscricao_estadual ?? "");
  const [consumidorFinal, setConsumidorFinal] = useState(cliente.consumidor_final);
  const [indicadorIe, setIndicadorIe] = useState(cliente.indicador_ie);
  const [observacoes, setObservacoes] = useState(cliente.observacoes ?? "");
  const [ativo, setAtivo] = useState(cliente.ativo);
  const [error, setError] = useState<string | null>(null);

  const salvar = useMutation({
    mutationFn: () =>
      api.patch(`/clientes/${cliente.id}`, {
        nome, tipo_pessoa: tipoPessoa,
        cpf_cnpj: cpfCnpj || null, rg: rg || null, apelido: apelido || null,
        telefone: telefone || null, celular: celular || null, email: email || null,
        cep: cep || null, endereco: endereco || null, cidade: cidade || null,
        uf: uf || null, inscricao_estadual: ie || null,
        consumidor_final: consumidorFinal, indicador_ie: indicadorIe,
        observacoes: observacoes || null, ativo,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["clientes"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-lg bg-[--color-surface] shadow-xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between border-b border-[--color-border] px-6 py-4 shrink-0">
          <h2 className="text-base font-semibold text-[--color-text-primary]">Editar cliente</h2>
          <button type="button" onClick={onClose} className="text-[--color-text-muted] hover:text-[--color-text-primary]">✕</button>
        </div>
        <form
          onSubmit={(e: FormEvent) => { e.preventDefault(); salvar.mutate(); }}
          className="px-6 py-4 space-y-4 overflow-y-auto"
        >
          {/* Dados básicos */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted]">Dados básicos</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2 space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Nome *</label>
                <input required value={nome} onChange={(e) => setNome(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Tipo de pessoa</label>
                <select value={tipoPessoa} onChange={(e) => setTipoPessoa(e.target.value)} className={INPUT_CLS}>
                  <option value="Fisica">Física</option>
                  <option value="Juridica">Jurídica</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">CPF/CNPJ</label>
                <input value={cpfCnpj} onChange={(e) => setCpfCnpj(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">RG</label>
                <input value={rg} onChange={(e) => setRg(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Apelido</label>
                <input value={apelido} onChange={(e) => setApelido(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Telefone</label>
                <input value={telefone} onChange={(e) => setTelefone(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Celular</label>
                <input value={celular} onChange={(e) => setCelular(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="col-span-2 space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">E-mail</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={INPUT_CLS} />
              </div>
            </div>
          </div>

          {/* Endereço */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted]">Endereço</p>
            <div className="grid grid-cols-4 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">CEP</label>
                <input value={cep} onChange={(e) => setCep(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="col-span-3 space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Endereço</label>
                <input value={endereco} onChange={(e) => setEndereco(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="col-span-3 space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Cidade</label>
                <input value={cidade} onChange={(e) => setCidade(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">UF</label>
                <input maxLength={2} value={uf} onChange={(e) => setUf(e.target.value.toUpperCase())} className={INPUT_CLS} />
              </div>
            </div>
          </div>

          {/* Fiscal */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted]">Fiscal</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Inscrição Estadual</label>
                <input value={ie} onChange={(e) => setIe(e.target.value)} className={INPUT_CLS} />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-[--color-text-primary]">Indicador de IE</label>
                <select value={indicadorIe} onChange={(e) => setIndicadorIe(e.target.value)} className={INPUT_CLS}>
                  <option value="1">1 – Contribuinte</option>
                  <option value="2">2 – Contribuinte isento</option>
                  <option value="9">9 – Não contribuinte</option>
                </select>
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-[--color-text-primary] cursor-pointer">
              <input type="checkbox" checked={consumidorFinal} onChange={(e) => setConsumidorFinal(e.target.checked)} className="rounded" />
              Consumidor final (NF-e)
            </label>
          </div>

          {/* Extras */}
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-sm font-medium text-[--color-text-primary]">Observações</label>
              <textarea rows={2} value={observacoes} onChange={(e) => setObservacoes(e.target.value)} className={INPUT_CLS} />
            </div>
            <label className="flex items-center gap-2 text-sm text-[--color-text-primary] cursor-pointer">
              <input type="checkbox" checked={ativo} onChange={(e) => setAtivo(e.target.checked)} className="rounded" />
              Ativo
            </label>
          </div>

          {error && <p className="text-sm text-[--color-error]">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={salvar.isPending}>
              {salvar.isPending ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────────

function ClientesPage() {
  const navigate = useNavigate();
  const [qInput, setQInput] = useState("");
  const [q, setQ] = useState("");
  const [tipoPessoa, setTipoPessoa] = useState("");
  const [ativoFiltro, setAtivoFiltro] = useState("");
  const [uf, setUf] = useState("");
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Cliente | null>(null);
  const [importResult, setImportResult] = useState<ImportacaoResult | null>(null);
  const [importVeicResult, setImportVeicResult] = useState<ImportacaoVeiculosResult | null>(null);
  const xlsxRef = useRef<HTMLInputElement>(null);
  const jsonRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  function pesquisar() { setQ(qInput); setPage(1); }
  function aplicarFiltro() { setPage(1); }

  const { data, isLoading } = useQuery({
    queryKey: ["clientes", q, tipoPessoa, ativoFiltro, uf, page],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (q) params.set("q", q);
      if (tipoPessoa) params.set("tipo_pessoa", tipoPessoa);
      if (ativoFiltro !== "") params.set("ativo", ativoFiltro);
      if (uf) params.set("uf", uf);
      return api.get<ClientesPaginados>(`/clientes?${params.toString()}`);
    },
    placeholderData: (prev) => prev,
  });

  const importar = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("arquivo", file);
      return api.postForm<ImportacaoResult>("/clientes/importar", form);
    },
    onSuccess: (res) => {
      setImportResult(res);
      void queryClient.invalidateQueries({ queryKey: ["clientes"] });
    },
    onError: (err: Error) => setImportResult({ criados: 0, atualizados: 0, ignorados: 0, erros: [err.message] }),
  });

  const importarVeiculos = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("arquivo", file);
      return api.postForm<ImportacaoVeiculosResult>("/clientes/importar-veiculos-json", form);
    },
    onSuccess: (res) => {
      setImportVeicResult(res);
      void queryClient.invalidateQueries({ queryKey: ["clientes"] });
    },
    onError: (err: Error) =>
      setImportVeicResult({
        match_cpf: 0, match_telefone: 0, match_nome: 0,
        clientes_nao_encontrados: 0, clientes_enriquecidos: 0,
        veiculos_upserted: 0, vinculos_criados: 0, placas_ignoradas: 0,
        erros: [err.message],
      }),
  });

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportResult(null);
    importar.mutate(file);
    e.target.value = "";
  }

  function handleJsonFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportVeicResult(null);
    importarVeiculos.mutate(file);
    e.target.value = "";
  }

  const clientes = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.pages ?? 1;

  return (
    <>
      {editando && <EditarClienteModal cliente={editando} onClose={() => setEditando(null)} />}
      <div className="p-8">
        {/* Cabeçalho */}
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-[--color-text-primary]">Clientes</h1>
          <div className="flex gap-2">
            <input ref={xlsxRef} type="file" accept=".xlsx" className="hidden" onChange={handleFile} />
            <input ref={jsonRef} type="file" accept=".json" className="hidden" onChange={handleJsonFile} />
            <Button size="sm" variant="outline" onClick={() => xlsxRef.current?.click()} disabled={importar.isPending}>
              {importar.isPending ? "Importando..." : "↑ Importar XLSX"}
            </Button>
            <Button size="sm" variant="outline" onClick={() => jsonRef.current?.click()} disabled={importarVeiculos.isPending}>
              {importarVeiculos.isPending ? "Importando..." : "↑ Importar Veículos JSON"}
            </Button>
            <Button size="sm" onClick={() => setShowForm((v) => !v)}>
              {showForm ? "Cancelar" : "+ Novo cliente"}
            </Button>
          </div>
        </div>

        {/* Resultado de importação XLSX */}
        {importResult && (
          <div className={`mb-4 rounded-md border px-4 py-3 text-sm ${importResult.erros.length > 0 ? "border-[--color-error] bg-[--color-error]/10" : "border-green-500 bg-green-500/10"}`}>
            <div className="flex items-start justify-between gap-2">
              <p className="font-medium">
                Importação de clientes — {importResult.criados} criados, {importResult.atualizados} atualizados, {importResult.ignorados} ignorados
              </p>
              <button type="button" onClick={() => setImportResult(null)} className="text-[--color-text-muted] hover:text-[--color-text-primary] shrink-0">✕</button>
            </div>
            {importResult.erros.length > 0 && (
              <ul className="list-disc list-inside text-[--color-error] space-y-0.5 mt-1">
                {importResult.erros.slice(0, 10).map((e, i) => <li key={i}>{e}</li>)}
                {importResult.erros.length > 10 && <li>…e mais {importResult.erros.length - 10} erros</li>}
              </ul>
            )}
          </div>
        )}

        {/* Resultado de importação de veículos JSON */}
        {importVeicResult && (
          <div className={`mb-4 rounded-md border px-4 py-3 text-sm ${importVeicResult.erros.length > 0 ? "border-[--color-error] bg-[--color-error]/10" : "border-green-500 bg-green-500/10"}`}>
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium mb-1">Importação de veículos concluída</p>
                <ul className="space-y-0.5 text-[--color-text-secondary]">
                  <li>{importVeicResult.veiculos_upserted} veículos cadastrados/atualizados</li>
                  <li>{importVeicResult.vinculos_criados} vínculos cliente-veículo criados</li>
                  <li>{importVeicResult.clientes_enriquecidos} clientes enriquecidos (apelido/cidade/telefone)</li>
                  <li className="pt-1 font-medium text-[--color-text-primary]">Clientes identificados por:</li>
                  <li className="pl-3">CPF/CNPJ: {importVeicResult.match_cpf}</li>
                  <li className="pl-3">Telefone: {importVeicResult.match_telefone}</li>
                  <li className="pl-3">Nome: {importVeicResult.match_nome}</li>
                  <li className="pl-3 text-[--color-error]">Não encontrados: {importVeicResult.clientes_nao_encontrados}</li>
                  <li>{importVeicResult.placas_ignoradas} placas ignoradas (inválidas)</li>
                </ul>
              </div>
              <button type="button" onClick={() => setImportVeicResult(null)} className="text-[--color-text-muted] hover:text-[--color-text-primary] shrink-0">✕</button>
            </div>
            {importVeicResult.erros.length > 0 && (
              <ul className="list-disc list-inside text-[--color-error] space-y-0.5 mt-2">
                {importVeicResult.erros.slice(0, 10).map((e, i) => <li key={i}>{e}</li>)}
                {importVeicResult.erros.length > 10 && <li>…e mais {importVeicResult.erros.length - 10} erros</li>}
              </ul>
            )}
          </div>
        )}

        {showForm && <NovoClienteForm onClose={() => setShowForm(false)} />}

        {/* Filtros */}
        <div className="mb-4 flex flex-wrap gap-2 items-center">
          <input
            type="search"
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && pesquisar()}
            placeholder="Nome, CPF, celular, apelido..."
            className="rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary] w-64"
          />
          <Button size="sm" variant="outline" onClick={pesquisar}>Buscar</Button>

          <select
            value={tipoPessoa}
            onChange={(e) => { setTipoPessoa(e.target.value); aplicarFiltro(); }}
            className="rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            <option value="">Tipo: Todos</option>
            <option value="Fisica">Física</option>
            <option value="Juridica">Jurídica</option>
          </select>

          <select
            value={ativoFiltro}
            onChange={(e) => { setAtivoFiltro(e.target.value); aplicarFiltro(); }}
            className="rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            <option value="">Status: Todos</option>
            <option value="true">Ativo</option>
            <option value="false">Inativo</option>
          </select>

          <input
            value={uf}
            onChange={(e) => { setUf(e.target.value.toUpperCase()); aplicarFiltro(); }}
            placeholder="UF"
            maxLength={2}
            className="w-16 rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />

          {total > 0 && (
            <span className="text-sm text-[--color-text-muted] ml-1">
              {total.toLocaleString("pt-BR")} clientes
            </span>
          )}
        </div>

        {/* Tabela */}
        <Card>
          <CardContent className="pt-4">
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : clientes.length === 0 ? (
              <p className="text-sm text-[--color-text-muted] py-4 text-center">Nenhum cliente encontrado.</p>
            ) : (
              <>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[--color-border] text-left text-[--color-text-muted]">
                      <th className="pb-2 pr-4 font-medium hidden sm:table-cell">CPF/CNPJ</th>
                      <th className="pb-2 pr-4 font-medium hidden sm:table-cell">Tipo</th>
                      <th className="pb-2 pr-4 font-medium">Nome</th>
                      <th className="pb-2 pr-4 font-medium hidden md:table-cell">Telefone</th>
                      <th className="pb-2 pr-4 font-medium hidden lg:table-cell">Cidade/UF</th>
                      <th className="pb-2 pr-4 font-medium">Status</th>
                      <th className="pb-2 font-medium">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[--color-border]">
                    {clientes.map((c) => (
                      <tr
                        key={c.id}
                        className="cursor-pointer hover:bg-[--color-background]"
                        onClick={() => void navigate({ to: "/app/clientes/$clienteId", params: { clienteId: c.id } })}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ")
                            void navigate({ to: "/app/clientes/$clienteId", params: { clienteId: c.id } });
                        }}
                      >
                        <td className="py-3 pr-4 font-mono text-xs text-[--color-text-secondary] hidden sm:table-cell">
                          {c.cpf_cnpj ?? "—"}
                        </td>
                        <td className="py-3 pr-4 hidden sm:table-cell">
                          <Badge variant={c.tipo_pessoa === "Juridica" ? "secondary" : "default"} className="text-xs">
                            {c.tipo_pessoa === "Juridica" ? "Jurídica" : "Física"}
                          </Badge>
                        </td>
                        <td className="py-3 pr-4 font-medium text-[--color-text-primary]">
                          {c.nome}
                          {c.apelido && <span className="ml-1 text-xs text-[--color-text-muted]">({c.apelido})</span>}
                        </td>
                        <td className="py-3 pr-4 text-[--color-text-secondary] hidden md:table-cell">
                          {c.celular ?? c.telefone ?? "—"}
                        </td>
                        <td className="py-3 pr-4 text-[--color-text-secondary] hidden lg:table-cell">
                          {c.cidade && c.uf ? `${c.cidade}/${c.uf}` : (c.cidade ?? c.uf ?? "—")}
                        </td>
                        <td className="py-3 pr-4">
                          <Badge variant={c.ativo ? "success" : "secondary"} className="text-xs">
                            {c.ativo ? "Ativo" : "Inativo"}
                          </Badge>
                        </td>
                        <td className="py-3" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center gap-3">
                            <Link
                              to="/app/clientes/$clienteId"
                              params={{ clienteId: c.id }}
                              className="text-xs text-[--color-primary] hover:underline whitespace-nowrap"
                            >
                              Ver
                            </Link>
                            {(c.celular ?? c.telefone) && (
                              <a
                                href={whatsappUrl((c.celular ?? c.telefone)!)}
                                target="_blank"
                                rel="noreferrer"
                                className="text-xs text-green-600 hover:underline"
                              >
                                WhatsApp
                              </a>
                            )}
                            <button
                              type="button"
                              onClick={() => setEditando(c)}
                              className="text-xs text-[--color-text-muted] hover:text-[--color-text-primary] hover:underline"
                            >
                              Editar
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-4 border-t border-[--color-border] mt-2">
                    <span className="text-sm text-[--color-text-muted]">Página {page} de {totalPages}</span>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                        ← Anterior
                      </Button>
                      <Button size="sm" variant="outline" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
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
