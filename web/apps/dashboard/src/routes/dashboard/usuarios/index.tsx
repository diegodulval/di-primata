import { formatDateTime, type PlatformUser } from "@di-mata/shared";
import { Badge, Card, CardContent, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/usuarios/")({
  component: UsuariosPage,
});

function useUsers() {
  return useQuery<PlatformUser[]>({
    queryKey: ["bff", "users"],
    queryFn: async () => {
      const token = sessionStorage.getItem("access_token");
      const res = await fetch("/api/bff/users", {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!res.ok) throw new Error("Erro ao carregar usuários");
      return res.json();
    },
    refetchInterval: 30_000,
  });
}

const ROLE_LABEL: Record<string, string> = {
  ADMIN: "Admin",
  OPERADOR: "Operador",
  CONSULTOR: "Consultor",
  PRODUTOR: "Produtor",
  CONSUMIDOR: "Consumidor",
};

const ROLE_VARIANT: Record<string, "default" | "secondary" | "outline" | "success" | "error"> = {
  ADMIN: "error",
  OPERADOR: "secondary",
  CONSULTOR: "outline",
  PRODUTOR: "success",
  CONSUMIDOR: "outline",
};

function UsuariosPage() {
  const { data: users, isLoading, isError } = useUsers();

  return (
    <div className="p-6 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[--color-text-primary]">Usuários</h1>
          <p className="text-sm text-[--color-text-muted] mt-1">
            Gestão de acesso e perfis da plataforma
          </p>
        </div>
        <Link
          to="/dashboard/usuarios/novo"
          className="inline-flex items-center gap-2 rounded-md bg-[--color-primary] px-4 py-2 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity"
        >
          + Novo usuário
        </Link>
      </header>

      {isError && (
        <p className="text-sm text-[--color-error]">Erro ao carregar dados.</p>
      )}

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      )}

      {users && users.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center space-y-3">
            <p className="text-[--color-text-muted] text-sm">
              Nenhum usuário cadastrado ainda.
            </p>
            <Link
              to="/dashboard/usuarios/novo"
              className="inline-flex items-center gap-1 text-sm text-[--color-primary] hover:underline"
            >
              Cadastrar o primeiro →
            </Link>
          </CardContent>
        </Card>
      )}

      {users && users.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-[--color-border]">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[--color-surface] border-b border-[--color-border]">
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">Usuário</th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">Organização</th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">Perfil</th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">Portal</th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">Cadastro</th>
                <th className="px-4 py-3 text-center font-medium text-[--color-text-muted]">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[--color-border]">
              {users.map((u) => (
                <tr
                  key={u.id}
                  className="bg-[--color-surface] hover:bg-[--color-background] transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-[--color-text-primary]">{u.nome}</div>
                    <div className="text-xs text-[--color-text-muted] mt-0.5">{u.email}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-[--color-text-secondary]">{u.account_nome}</div>
                    {u.setor_primario && (
                      <div className="text-xs text-[--color-text-muted] mt-0.5 capitalize">
                        {u.setor_primario}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {u.role ? (
                      <Badge variant={ROLE_VARIANT[u.role] ?? "outline"}>
                        {ROLE_LABEL[u.role] ?? u.role}
                      </Badge>
                    ) : (
                      <span className="text-[--color-text-muted]">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {u.portal_access ? (
                      <Badge variant="default">Habilitado</Badge>
                    ) : (
                      <span className="text-xs text-[--color-text-muted]">Sem acesso</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-[--color-text-muted] whitespace-nowrap">
                    {formatDateTime(u.criado_em)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <Badge variant={u.ativo ? "success" : "error"}>
                      {u.ativo ? "Ativo" : "Inativo"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
