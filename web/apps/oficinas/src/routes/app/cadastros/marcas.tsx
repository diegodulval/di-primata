import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/cadastros/marcas")({
  component: MarcasPage,
});

const INPUT_CLS =
  "w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]";

interface Marca {
  id: string;
  tenant_id: string;
  nome: string;
  ativo: boolean;
}

// ─── Nova marca (form inline) ─────────────────────────────────────────────────

function NovaMarcaForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState("");
  const [error, setError] = useState<string | null>(null);

  const criar = useMutation({
    mutationFn: () => api.post<Marca>("/marcas", { nome: nome.trim() }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["marcas"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <form
      onSubmit={(e: FormEvent) => {
        e.preventDefault();
        criar.mutate();
      }}
      className="flex items-end gap-3 p-4 bg-[var(--color-surface)] rounded-lg border border-[--color-border]"
    >
      <div className="flex-1 space-y-1">
        <label className="text-sm font-medium text-[--color-text-primary]">
          Nome da marca *
        </label>
        <input
          required
          autoFocus
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          placeholder="Ex: Bosch, NGK, Mahle..."
          className={INPUT_CLS}
        />
        {error && <p className="text-xs text-[--color-error]">{error}</p>}
      </div>
      <div className="flex gap-2 pb-0.5">
        <Button type="button" variant="outline" size="sm" onClick={onClose}>
          Cancelar
        </Button>
        <Button type="submit" size="sm" disabled={criar.isPending || !nome.trim()}>
          {criar.isPending ? "Salvando..." : "Salvar"}
        </Button>
      </div>
    </form>
  );
}

// ─── Editar marca (modal) ─────────────────────────────────────────────────────

function EditarMarcaModal({ marca, onClose }: { marca: Marca; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState(marca.nome);
  const [error, setError] = useState<string | null>(null);

  const salvar = useMutation({
    mutationFn: () => api.patch(`/marcas/${marca.id}`, { nome: nome.trim() }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["marcas"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  const toggleAtivo = useMutation({
    mutationFn: () => api.patch(`/marcas/${marca.id}`, { ativo: !marca.ativo }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["marcas"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-lg bg-[var(--color-surface)] shadow-xl">
        <div className="flex items-center justify-between border-b border-[--color-border] px-6 py-4">
          <h2 className="text-base font-semibold text-[--color-text-primary]">Editar marca</h2>
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
          className="px-6 py-4 space-y-4"
        >
          <div className="space-y-1">
            <label className="text-sm font-medium text-[--color-text-primary]">Nome *</label>
            <input
              required
              autoFocus
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              className={INPUT_CLS}
            />
          </div>

          {error && <p className="text-sm text-[--color-error]">{error}</p>}

          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={() => toggleAtivo.mutate()}
              disabled={toggleAtivo.isPending}
              className={`text-sm underline-offset-2 hover:underline disabled:opacity-50 ${marca.ativo ? "text-[--color-error]" : "text-[--color-primary]"}`}
            >
              {marca.ativo ? "Desativar" : "Reativar"}
            </button>
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={onClose}>
                Cancelar
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={salvar.isPending || !nome.trim()}
              >
                {salvar.isPending ? "Salvando..." : "Salvar"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

interface MarcasPaginadas {
  items: Marca[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const PAGE_SIZE = 20;

// ─── MarcasPage ───────────────────────────────────────────────────────────────

function MarcasPage() {
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Marca | null>(null);
  const [q, setQ] = useState("");
  const [qInput, setQInput] = useState("");
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["marcas", "lista", q, page],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (q) params.set("q", q);
      return api.get<MarcasPaginadas>(`/marcas?${params.toString()}`);
    },
    placeholderData: (prev) => prev,
  });

  const marcas = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.pages ?? 1;

  function pesquisar() {
    setQ(qInput);
    setPage(1);
  }

  return (
    <>
      {editando && (
        <EditarMarcaModal marca={editando} onClose={() => setEditando(null)} />
      )}

      <div className="p-8 max-w-2xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[--color-text-primary]">Marcas</h1>
            {!isLoading && total > 0 && (
              <p className="text-sm text-[--color-text-muted] mt-0.5">
                {total} marca{total !== 1 ? "s" : ""}
              </p>
            )}
          </div>
          <Button
            size="sm"
            onClick={() => {
              setShowForm((v) => !v);
              void queryClient.invalidateQueries({ queryKey: ["marcas", "lista"] });
            }}
          >
            {showForm ? "Cancelar" : "+ Nova marca"}
          </Button>
        </div>

        {showForm && (
          <div className="mb-4">
            <NovaMarcaForm onClose={() => { setShowForm(false); setPage(1); }} />
          </div>
        )}

        <div className="mb-4 flex gap-2">
          <input
            type="search"
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && pesquisar()}
            placeholder="Buscar por nome..."
            className="flex-1 rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
          />
          <Button size="sm" variant="outline" onClick={pesquisar}>
            Buscar
          </Button>
        </div>

        <Card>
          <CardContent className="pt-4">
            {isLoading ? (
              <div className="space-y-2 py-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-10 rounded-md bg-[--color-border] animate-pulse" />
                ))}
              </div>
            ) : marcas.length === 0 ? (
              <p className="text-sm text-[--color-text-muted] py-6 text-center">
                {q ? "Nenhuma marca encontrada." : "Nenhuma marca cadastrada."}
              </p>
            ) : (
              <>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[--color-border] text-left text-[--color-text-muted]">
                      <th className="pb-2 font-medium">Nome</th>
                      <th className="pb-2 font-medium text-center w-24">Status</th>
                      <th className="pb-2 font-medium text-right w-20">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[--color-border]">
                    {marcas.map((m) => (
                      <tr key={m.id} className={!m.ativo ? "opacity-50" : ""}>
                        <td className="py-3 text-[--color-text-primary] font-medium">
                          {m.nome}
                        </td>
                        <td className="py-3 text-center">
                          {m.ativo ? (
                            <Badge variant="success" className="text-xs">Ativa</Badge>
                          ) : (
                            <Badge variant="warning" className="text-xs">Inativa</Badge>
                          )}
                        </td>
                        <td className="py-3 text-right">
                          <Button size="sm" variant="outline" onClick={() => setEditando(m)}>
                            Editar
                          </Button>
                        </td>
                      </tr>
                    ))}
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
