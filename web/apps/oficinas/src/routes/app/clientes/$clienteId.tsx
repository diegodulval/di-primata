import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/clientes/$clienteId")({
  component: ClienteDetalhe,
});

interface Cliente {
  id: string;
  nome: string;
  cpf_cnpj: string | null;
  telefone: string | null;
  email: string | null;
  endereco: string | null;
}

interface ClienteVeiculo {
  id: string;
  veiculo_id: string;
  data_inicio: string;
  data_fim: string | null;
  ativo: boolean;
}

function VincularVeiculoForm({
  clienteId,
  onClose,
}: {
  clienteId: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [placa, setPlaca] = useState("");
  const [error, setError] = useState<string | null>(null);

  const vincular = useMutation({
    mutationFn: async () => {
      const veiculo = await api.get<{ id: string }>(
        `/veiculos/${encodeURIComponent(placa.toUpperCase())}`
      );
      await api.post(`/clientes/${clienteId}/veiculos`, { veiculo_id: veiculo.id });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cliente-veiculos", clienteId] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <form
      onSubmit={(e: FormEvent) => {
        e.preventDefault();
        vincular.mutate();
      }}
      className="flex gap-2 items-end mt-4"
    >
      <div className="space-y-1 flex-1 max-w-xs">
        <label htmlFor="placa-vincular" className="text-sm font-medium text-[--color-text-primary]">
          Placa
        </label>
        <input
          id="placa-vincular"
          required
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          placeholder="ABC1234 ou ABC1D23"
          maxLength={8}
          className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
      </div>
      <Button type="submit" size="sm" disabled={vincular.isPending}>
        {vincular.isPending ? "Vinculando..." : "Vincular"}
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={onClose}>
        Cancelar
      </Button>
      {error && <p className="text-sm text-[--color-error] self-center">{error}</p>}
    </form>
  );
}

function ClienteDetalhe() {
  const { clienteId } = Route.useParams();
  const queryClient = useQueryClient();
  const [showVincular, setShowVincular] = useState(false);

  const { data: cliente, isLoading } = useQuery({
    queryKey: ["cliente", clienteId],
    queryFn: () => api.get<Cliente>(`/clientes/${clienteId}`),
  });

  const { data: veiculos, isLoading: loadingVeiculos } = useQuery({
    queryKey: ["cliente-veiculos", clienteId],
    queryFn: () => api.get<ClienteVeiculo[]>(`/clientes/${clienteId}/veiculos`),
  });

  const desassociar = useMutation({
    mutationFn: (veiculoId: string) => api.delete(`/clientes/${clienteId}/veiculos/${veiculoId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cliente-veiculos", clienteId] });
    },
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to="/app/clientes"
          className="text-sm text-[--color-text-muted] hover:text-[--color-text-primary]"
        >
          ← Clientes
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{isLoading ? <Skeleton className="h-6 w-48" /> : cliente?.nome}</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-64" />
              <Skeleton className="h-4 w-48" />
            </div>
          ) : (
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 text-sm">
              <div>
                <dt className="text-[--color-text-muted]">CPF/CNPJ</dt>
                <dd className="text-[--color-text-primary]">{cliente?.cpf_cnpj ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[--color-text-muted]">Telefone</dt>
                <dd className="text-[--color-text-primary]">{cliente?.telefone ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[--color-text-muted]">E-mail</dt>
                <dd className="text-[--color-text-primary]">{cliente?.email ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[--color-text-muted]">Endereço</dt>
                <dd className="text-[--color-text-primary]">{cliente?.endereco ?? "—"}</dd>
              </div>
            </dl>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Veículos</CardTitle>
          <Button size="sm" variant="outline" onClick={() => setShowVincular((v) => !v)}>
            {showVincular ? "Cancelar" : "+ Vincular"}
          </Button>
        </CardHeader>
        <CardContent>
          {showVincular && (
            <VincularVeiculoForm clienteId={clienteId} onClose={() => setShowVincular(false)} />
          )}
          {loadingVeiculos ? (
            <div className="space-y-2 mt-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : veiculos?.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] py-4 text-center">
              Nenhum veículo vinculado.
            </p>
          ) : (
            <table className="w-full text-sm mt-4">
              <thead>
                <tr className="border-b border-[--color-border] text-left text-[--color-text-muted]">
                  <th className="pb-2 pr-4 font-medium">Veículo ID</th>
                  <th className="pb-2 pr-4 font-medium">Desde</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-border]">
                {veiculos?.map((v) => (
                  <tr key={v.id}>
                    <td className="py-3 pr-4 font-mono text-xs text-[--color-text-secondary]">
                      {v.veiculo_id.slice(0, 8)}…
                    </td>
                    <td className="py-3 pr-4 text-[--color-text-secondary]">{v.data_inicio}</td>
                    <td className="py-3 pr-4">
                      <Badge variant={v.ativo ? "success" : "secondary"}>
                        {v.ativo ? "Ativo" : "Encerrado"}
                      </Badge>
                    </td>
                    <td className="py-3 text-right">
                      {v.ativo && (
                        <button
                          type="button"
                          onClick={() => desassociar.mutate(v.veiculo_id)}
                          className="text-xs text-[--color-error] hover:underline"
                        >
                          Desassociar
                        </button>
                      )}
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
