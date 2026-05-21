import { api } from "@/lib/api";
import { Badge, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/usuarios/")({
  component: UsuariosPage,
});

interface Usuario {
  id: string;
  nome: string;
  email: string | null;
  perfil: string;
  numero_whatsapp: string | null;
  ativo: boolean;
}

interface UsuarioList {
  total: number;
  items: Usuario[];
}

const PERFIL_LABEL: Record<string, string> = {
  ADMIN: "Admin",
  ATENDENTE: "Atendente",
  MECANICO: "Mecânico",
};

function UsuariosPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["usuarios"],
    queryFn: () => api.get<UsuarioList>("/usuarios"),
  });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[--color-text-primary] mb-6">Usuários</h1>
      <Card>
        <CardHeader>
          <CardTitle>Equipe ({data?.total ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[--color-border] text-left text-[--color-text-muted]">
                  <th className="pb-2 pr-4 font-medium">Nome</th>
                  <th className="pb-2 pr-4 font-medium">Contato</th>
                  <th className="pb-2 pr-4 font-medium">Perfil</th>
                  <th className="pb-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-border]">
                {data?.items.map((u) => (
                  <tr key={u.id}>
                    <td className="py-3 pr-4 font-medium text-[--color-text-primary]">{u.nome}</td>
                    <td className="py-3 pr-4 text-[--color-text-secondary]">
                      {u.email ?? u.numero_whatsapp ?? "—"}
                    </td>
                    <td className="py-3 pr-4">
                      <Badge variant="outline">{PERFIL_LABEL[u.perfil] ?? u.perfil}</Badge>
                    </td>
                    <td className="py-3">
                      <Badge variant={u.ativo ? "success" : "secondary"}>
                        {u.ativo ? "Ativo" : "Inativo"}
                      </Badge>
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
