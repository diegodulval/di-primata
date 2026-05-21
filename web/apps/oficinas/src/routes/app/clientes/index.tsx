import { api } from "@/lib/api";
import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/clientes/")({
  component: ClientesPage,
});

interface Cliente {
  id: string;
  nome: string;
  cpf_cnpj: string | null;
  telefone: string | null;
  email: string | null;
}

interface ClienteList {
  total: number;
  items: Cliente[];
}

function NovoClienteForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState("");
  const [cpf, setCpf] = useState("");
  const [telefone, setTelefone] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);

  const criar = useMutation({
    mutationFn: () =>
      api.post("/clientes", {
        nome,
        cpf_cnpj: cpf || null,
        telefone: telefone || null,
        email: email || null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["clientes"] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Novo cliente</CardTitle>
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
              <label htmlFor="nc-nome" className="text-sm font-medium text-[--color-text-primary]">
                Nome *
              </label>
              <input
                id="nc-nome"
                required
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="nc-cpf" className="text-sm font-medium text-[--color-text-primary]">
                CPF/CNPJ
              </label>
              <input
                id="nc-cpf"
                value={cpf}
                onChange={(e) => setCpf(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="nc-tel" className="text-sm font-medium text-[--color-text-primary]">
                Telefone
              </label>
              <input
                id="nc-tel"
                value={telefone}
                onChange={(e) => setTelefone(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="nc-email" className="text-sm font-medium text-[--color-text-primary]">
                E-mail
              </label>
              <input
                id="nc-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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

function ClientesPage() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["clientes", q],
    queryFn: () => api.get<ClienteList>(`/clientes${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Clientes</h1>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancelar" : "+ Novo cliente"}
        </Button>
      </div>

      {showForm && <NovoClienteForm onClose={() => setShowForm(false)} />}

      <div className="mb-4">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar por nome, CPF ou telefone..."
          className="w-full max-w-sm rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
      </div>

      <Card>
        <CardContent className="pt-4">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : data?.items.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] py-4 text-center">
              Nenhum cliente encontrado.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[--color-border] text-left text-[--color-text-muted]">
                  <th className="pb-2 pr-4 font-medium">Nome</th>
                  <th className="pb-2 pr-4 font-medium hidden sm:table-cell">CPF/CNPJ</th>
                  <th className="pb-2 pr-4 font-medium hidden md:table-cell">Telefone</th>
                  <th className="pb-2 font-medium hidden md:table-cell">E-mail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-border]">
                {data?.items.map((c) => (
                  <tr
                    key={c.id}
                    className="cursor-pointer hover:bg-[--color-background]"
                    onClick={() =>
                      void navigate({ to: "/app/clientes/$clienteId", params: { clienteId: c.id } })
                    }
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ")
                        void navigate({
                          to: "/app/clientes/$clienteId",
                          params: { clienteId: c.id },
                        });
                    }}
                  >
                    <td className="py-3 pr-4 font-medium text-[--color-text-primary]">{c.nome}</td>
                    <td className="py-3 pr-4 text-[--color-text-secondary] hidden sm:table-cell">
                      {c.cpf_cnpj ?? "—"}
                    </td>
                    <td className="py-3 pr-4 text-[--color-text-secondary] hidden md:table-cell">
                      {c.telefone ?? "—"}
                    </td>
                    <td className="py-3 text-[--color-text-secondary] hidden md:table-cell">
                      {c.email ?? "—"}
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
