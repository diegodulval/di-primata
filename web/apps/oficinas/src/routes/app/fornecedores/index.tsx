import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { type FormEvent, useRef, useState } from "react";

export const Route = createFileRoute("/app/fornecedores/")({
  component: FornecedoresPage,
});

interface Fornecedor {
  id: string;
  razao_social: string;
  nome_fantasia: string | null;
  cnpj: string | null;
  inscricao_estadual: string | null;
  telefone: string | null;
  email: string | null;
  contato: string | null;
  ativo: boolean;
  tipo_pessoa: string | null;
}

type TipoPessoa = "Juridica" | "Fisica";
type FiltroAtivo = "todos" | "ativo" | "inativo";

// ─── Formulário ───────────────────────────────────────────────────────────────

interface FormDados {
  razao_social: string;
  nome_fantasia: string | null;
  cnpj: string | null;
  inscricao_estadual: string | null;
  telefone: string | null;
  email: string | null;
  ativo: boolean;
  tipo_pessoa: TipoPessoa;
}

function FornecedorForm({
  initial,
  onSave,
  onCancel,
  isPending,
  erro,
}: {
  initial?: Fornecedor;
  onSave: (dados: FormDados) => void;
  onCancel: () => void;
  isPending: boolean;
  erro: string | null;
}) {
  const [razaoSocial, setRazaoSocial] = useState(initial?.razao_social ?? "");
  const [nomeFantasia, setNomeFantasia] = useState(initial?.nome_fantasia ?? "");
  const [cnpj, setCnpj] = useState(initial?.cnpj ?? "");
  const [inscricaoEstadual, setInscricaoEstadual] = useState(initial?.inscricao_estadual ?? "");
  const [telefone, setTelefone] = useState(initial?.telefone ?? "");
  const [email, setEmail] = useState(initial?.email ?? "");
  const [ativo, setAtivo] = useState(initial?.ativo ?? true);
  const [tipoPessoa, setTipoPessoa] = useState<TipoPessoa>(
    (initial?.tipo_pessoa as TipoPessoa) ?? "Juridica",
  );

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSave({
      razao_social: razaoSocial,
      nome_fantasia: nomeFantasia || null,
      cnpj: cnpj || null,
      inscricao_estadual: inscricaoEstadual || null,
      telefone: telefone || null,
      email: email || null,
      ativo,
      tipo_pessoa: tipoPessoa,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="sm:col-span-2 space-y-1">
          <label className="text-sm font-medium text-[--color-text-primary]">Razão Social *</label>
          <input
            required
            value={razaoSocial}
            onChange={(e) => setRazaoSocial(e.target.value)}
            className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-[--color-text-primary]">Nome Fantasia</label>
          <input
            value={nomeFantasia}
            onChange={(e) => setNomeFantasia(e.target.value)}
            className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-[--color-text-primary]">Tipo de Pessoa</label>
          <select
            value={tipoPessoa}
            onChange={(e) => setTipoPessoa(e.target.value as TipoPessoa)}
            className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            <option value="Juridica">Jurídica</option>
            <option value="Fisica">Física</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-[--color-text-primary]">CNPJ / CPF</label>
          <input
            value={cnpj}
            onChange={(e) => setCnpj(e.target.value)}
            placeholder="00.000.000/0000-00"
            className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-[--color-text-primary]">
            Inscrição Estadual
          </label>
          <input
            value={inscricaoEstadual}
            onChange={(e) => setInscricaoEstadual(e.target.value)}
            className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-[--color-text-primary]">Telefone</label>
          <input
            value={telefone}
            onChange={(e) => setTelefone(e.target.value)}
            placeholder="(00) 0000-0000"
            className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-[--color-text-primary]">E-mail</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="flex items-center gap-2 pt-4">
          <input
            id="f-ativo"
            type="checkbox"
            checked={ativo}
            onChange={(e) => setAtivo(e.target.checked)}
            className="rounded"
          />
          <label htmlFor="f-ativo" className="text-sm text-[--color-text-primary]">
            Fornecedor ativo
          </label>
        </div>
      </div>
      {erro && <p className="text-sm text-[--color-error]">{erro}</p>}
      <div className="flex gap-2 justify-end">
        <Button type="button" variant="outline" size="sm" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" size="sm" disabled={isPending}>
          {isPending ? "Salvando..." : "Salvar"}
        </Button>
      </div>
    </form>
  );
}

// ─── Modal de edição ──────────────────────────────────────────────────────────

function EditarModal({
  fornecedor,
  onClose,
}: {
  fornecedor: Fornecedor;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [erro, setErro] = useState<string | null>(null);

  const atualizar = useMutation({
    mutationFn: (dados: FormDados) => api.patch(`/fornecedores/${fornecedor.id}`, dados),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fornecedores"] });
      onClose();
    },
    onError: (err: Error) => setErro(err.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-[var(--color-surface)] rounded-lg shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto space-y-4">
        <h2 className="text-base font-semibold text-[--color-text-primary]">Editar Fornecedor</h2>
        <FornecedorForm
          initial={fornecedor}
          onSave={(dados) => atualizar.mutate(dados)}
          onCancel={onClose}
          isPending={atualizar.isPending}
          erro={erro}
        />
      </div>
    </div>
  );
}

// ─── Página principal ─────────────────────────────────────────────────────────

interface ImportacaoResultado {
  criados: number;
  atualizados: number;
  ignorados: number;
  erros: string[];
}

function FornecedoresPage() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [filtroAtivo, setFiltroAtivo] = useState<FiltroAtivo>("todos");
  const [filtroTipo, setFiltroTipo] = useState<"todos" | TipoPessoa>("todos");
  const [showForm, setShowForm] = useState(false);
  const [erroCreate, setErroCreate] = useState<string | null>(null);
  const [editando, setEditando] = useState<Fornecedor | null>(null);
  const [importando, setImportando] = useState(false);
  const [resultadoImport, setResultadoImport] = useState<ImportacaoResultado | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (filtroAtivo === "ativo") params.set("ativo", "true");
  if (filtroAtivo === "inativo") params.set("ativo", "false");
  if (filtroTipo !== "todos") params.set("tipo_pessoa", filtroTipo);

  const { data: fornecedores, isLoading } = useQuery({
    queryKey: ["fornecedores", q, filtroAtivo, filtroTipo],
    queryFn: () => api.get<Fornecedor[]>(`/fornecedores?${params.toString()}`),
  });

  async function handleImportarXlsx(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportando(true);
    setResultadoImport(null);
    try {
      const form = new FormData();
      form.append("arquivo", file);
      const resultado = await api.postForm<ImportacaoResultado>("/fornecedores/importar", form);
      setResultadoImport(resultado);
      void queryClient.invalidateQueries({ queryKey: ["fornecedores"] });
    } catch (err) {
      setResultadoImport({ criados: 0, atualizados: 0, ignorados: 0, erros: [String(err)] });
    } finally {
      setImportando(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const criar = useMutation({
    mutationFn: (dados: FormDados) => api.post<Fornecedor>("/fornecedores", dados),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fornecedores"] });
      setShowForm(false);
      setErroCreate(null);
    },
    onError: (err: Error) => setErroCreate(err.message),
  });

  return (
    <div className="p-8 space-y-6">
      {editando && <EditarModal fornecedor={editando} onClose={() => setEditando(null)} />}

      {/* ── Cabeçalho ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Fornecedores</h1>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={handleImportarXlsx}
          />
          <Button
            size="sm"
            variant="outline"
            disabled={importando}
            onClick={() => fileInputRef.current?.click()}
          >
            {importando ? "Importando..." : "↑ Importar XLSX"}
          </Button>
          <Button size="sm" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancelar" : "+ Novo Fornecedor"}
          </Button>
        </div>
      </div>

      {/* ── Resultado da importação ───────────────────────────────────────── */}
      {resultadoImport && (
        <div className={`rounded-md border px-4 py-3 text-sm space-y-1 ${resultadoImport.erros.length > 0 ? "border-[--color-warning] bg-[--color-warning]/10" : "border-[--color-success] bg-[--color-success]/10"}`}>
          <div className="flex items-center justify-between">
            <p className="font-medium text-[--color-text-primary]">
              Importação concluída — {resultadoImport.criados} criados, {resultadoImport.atualizados} atualizados, {resultadoImport.ignorados} ignorados
            </p>
            <button
              type="button"
              onClick={() => setResultadoImport(null)}
              className="text-xs text-[--color-text-muted] hover:text-[--color-text-primary]"
            >
              ✕
            </button>
          </div>
          {resultadoImport.erros.length > 0 && (
            <ul className="text-xs text-[--color-error] space-y-0.5 list-disc list-inside">
              {resultadoImport.erros.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
        </div>
      )}

      {/* ── Formulário de criação ──────────────────────────────────────────── */}
      {showForm && (
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm font-medium text-[--color-text-primary] mb-4">Novo Fornecedor</p>
            <FornecedorForm
              onSave={(dados) => criar.mutate(dados)}
              onCancel={() => {
                setShowForm(false);
                setErroCreate(null);
              }}
              isPending={criar.isPending}
              erro={erroCreate}
            />
          </CardContent>
        </Card>
      )}

      {/* ── Filtros ───────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Pesquise por Nome Fantasia, CPF/CNPJ ou Razão Social"
          className="flex-1 min-w-56 rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <div className="flex items-center gap-2">
          <label className="text-xs text-[--color-text-muted]">Status:</label>
          <select
            value={filtroAtivo}
            onChange={(e) => setFiltroAtivo(e.target.value as FiltroAtivo)}
            className="rounded-md border border-[--color-border] bg-[var(--color-surface)] px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            <option value="todos">Todos</option>
            <option value="ativo">Ativo</option>
            <option value="inativo">Inativo</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-[--color-text-muted]">Tipo:</label>
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value as "todos" | TipoPessoa)}
            className="rounded-md border border-[--color-border] bg-[var(--color-surface)] px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          >
            <option value="todos">Todos</option>
            <option value="Juridica">Jurídica</option>
            <option value="Fisica">Física</option>
          </select>
        </div>
      </div>

      {/* ── Tabela ────────────────────────────────────────────────────────── */}
      <Card>
        <CardContent className="p-0 overflow-x-auto">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !fornecedores?.length ? (
            <p className="text-sm text-[--color-text-muted] py-10 text-center">
              {q || filtroAtivo !== "todos" || filtroTipo !== "todos"
                ? "Nenhum fornecedor encontrado."
                : "Nenhum fornecedor cadastrado."}
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[var(--color-surface)] border-b border-[--color-border] text-xs font-medium text-[--color-text-muted] text-left">
                  <th className="px-4 py-3">CPF/CNPJ</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">Nome/Razão Social</th>
                  <th className="px-4 py-3">Nome Fantasia</th>
                  <th className="px-4 py-3">Telefone</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-border]">
                {fornecedores.map((f) => (
                  <tr key={f.id} className="bg-[var(--color-surface)] hover:bg-[var(--color-background)] transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-[--color-text-muted]">
                      {f.cnpj ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={f.tipo_pessoa === "Fisica" ? "secondary" : "default"}>
                        {f.tipo_pessoa === "Fisica" ? "Física" : "Jurídica"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 font-medium text-[--color-text-primary] max-w-xs truncate">
                      {f.razao_social}
                    </td>
                    <td className="px-4 py-3 text-[--color-text-secondary] max-w-xs truncate">
                      {f.nome_fantasia ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-[--color-text-secondary]">
                      {f.telefone ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={f.ativo ? "success" : "error"}>
                        {f.ativo ? "Ativo" : "Inativo"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <Link
                          to="/app/fornecedores/$fornecedorId"
                          params={{ fornecedorId: f.id }}
                          className="text-xs text-[--color-text-muted] hover:text-[--color-primary] transition-colors"
                        >
                          Produtos
                        </Link>
                        <button
                          type="button"
                          onClick={() => setEditando(f)}
                          className="text-xs text-[--color-text-muted] hover:text-[--color-primary] transition-colors"
                        >
                          Editar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
