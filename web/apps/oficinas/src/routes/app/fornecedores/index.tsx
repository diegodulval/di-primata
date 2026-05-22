import { api } from "@/lib/api";
import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/fornecedores/")({
  component: FornecedoresPage,
});

interface Fornecedor {
  id: string;
  razao_social: string;
  cnpj: string | null;
  contato: string | null;
}

// ─── Formulário compartilhado ─────────────────────────────────────────────────

interface FornecedorFormProps {
  initial?: Fornecedor;
  onSave: (dados: { razao_social: string; cnpj: string | null; contato: string | null }) => void;
  onCancel: () => void;
  isPending: boolean;
  erro: string | null;
}

function FornecedorForm({ initial, onSave, onCancel, isPending, erro }: FornecedorFormProps) {
  const [razaoSocial, setRazaoSocial] = useState(initial?.razao_social ?? "");
  const [cnpj, setCnpj] = useState(initial?.cnpj ?? "");
  const [contato, setContato] = useState(initial?.contato ?? "");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSave({
      razao_social: razaoSocial,
      cnpj: cnpj || null,
      contato: contato || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="sm:col-span-2 space-y-1">
          <label htmlFor="f-razao" className="text-sm font-medium text-[--color-text-primary]">
            Razão social *
          </label>
          <input
            id="f-razao"
            required
            value={razaoSocial}
            onChange={(e) => setRazaoSocial(e.target.value)}
            className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="f-cnpj" className="text-sm font-medium text-[--color-text-primary]">
            CNPJ
          </label>
          <input
            id="f-cnpj"
            value={cnpj}
            onChange={(e) => setCnpj(e.target.value)}
            placeholder="00.000.000/0000-00"
            className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="f-contato" className="text-sm font-medium text-[--color-text-primary]">
            Contato
          </label>
          <input
            id="f-contato"
            value={contato}
            onChange={(e) => setContato(e.target.value)}
            placeholder="Telefone, e-mail ou nome"
            className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
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

// ─── Linha editável ────────────────────────────────────────────────────────────

function FornecedorRow({ fornecedor }: { fornecedor: Fornecedor }) {
  const queryClient = useQueryClient();
  const [editando, setEditando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const atualizar = useMutation({
    mutationFn: (dados: { razao_social: string; cnpj: string | null; contato: string | null }) =>
      api.patch<Fornecedor>(`/fornecedores/${fornecedor.id}`, dados),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fornecedores"] });
      setEditando(false);
      setErro(null);
    },
    onError: (err: Error) => setErro(err.message),
  });

  if (editando) {
    return (
      <div className="px-4 py-3 border-b border-[--color-border] last:border-0">
        <p className="text-xs text-[--color-text-muted] mb-3">Editando fornecedor</p>
        <FornecedorForm
          initial={fornecedor}
          onSave={(dados) => atualizar.mutate(dados)}
          onCancel={() => {
            setEditando(false);
            setErro(null);
          }}
          isPending={atualizar.isPending}
          erro={erro}
        />
      </div>
    );
  }

  return (
    <div className="px-4 py-3 border-b border-[--color-border] last:border-0 flex items-center justify-between gap-4">
      <div className="min-w-0">
        <p className="text-sm font-medium text-[--color-text-primary] truncate">
          {fornecedor.razao_social}
        </p>
        <div className="flex gap-4 mt-0.5 flex-wrap">
          {fornecedor.cnpj && (
            <span className="text-xs font-mono text-[--color-text-muted]">{fornecedor.cnpj}</span>
          )}
          {fornecedor.contato && (
            <span className="text-xs text-[--color-text-secondary]">{fornecedor.contato}</span>
          )}
          {!fornecedor.cnpj && !fornecedor.contato && (
            <span className="text-xs text-[--color-text-muted]">Sem dados de contato</span>
          )}
        </div>
      </div>
      <Button size="sm" variant="outline" onClick={() => setEditando(true)} className="shrink-0">
        Editar
      </Button>
    </div>
  );
}

// ─── Página principal ─────────────────────────────────────────────────────────

function FornecedoresPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [erroCreate, setErroCreate] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const { data: fornecedores, isLoading } = useQuery({
    queryKey: ["fornecedores"],
    queryFn: () => api.get<Fornecedor[]>("/fornecedores"),
  });

  const criar = useMutation({
    mutationFn: (dados: { razao_social: string; cnpj: string | null; contato: string | null }) =>
      api.post<Fornecedor>("/fornecedores", dados),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fornecedores"] });
      setShowForm(false);
      setErroCreate(null);
    },
    onError: (err: Error) => setErroCreate(err.message),
  });

  const filtrados =
    fornecedores?.filter((f) => {
      if (!q) return true;
      const lower = q.toLowerCase();
      return (
        f.razao_social.toLowerCase().includes(lower) ||
        (f.cnpj ?? "").includes(q) ||
        (f.contato ?? "").toLowerCase().includes(lower)
      );
    }) ?? [];

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Fornecedores</h1>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancelar" : "+ Novo fornecedor"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Novo fornecedor</CardTitle>
          </CardHeader>
          <CardContent>
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

      <div>
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar por razão social, CNPJ ou contato..."
          className="w-full max-w-sm rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : filtrados.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] py-8 text-center">
              {q ? "Nenhum fornecedor encontrado." : "Nenhum fornecedor cadastrado."}
            </p>
          ) : (
            filtrados.map((f) => <FornecedorRow key={f.id} fornecedor={f} />)
          )}
        </CardContent>
      </Card>
    </div>
  );
}
