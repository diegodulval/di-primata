import { api } from "@di-mata/api-client";
import { formatDateTime } from "@di-mata/shared";
import type { EstadoAgente } from "@di-mata/shared";
import { Badge } from "@di-mata/ui";
import { Card, CardContent } from "@di-mata/ui";
import { Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/whatsapp/")({
  component: WhatsappSessions,
});

const ESTADO_BADGE: Record<
  EstadoAgente,
  { label: string; variant: "default" | "secondary" | "outline" | "success" | "warning" | "error" }
> = {
  OCIOSO: { label: "Ocioso", variant: "secondary" },
  ESCUTANDO: { label: "Escutando", variant: "outline" },
  PROCESSANDO: { label: "Processando", variant: "warning" },
  AGUARD_CONFIRM: { label: "Aguard. confirm", variant: "default" },
  SINCRONIZANDO: { label: "Sincronizando", variant: "default" },
  OFFLINE: { label: "Offline", variant: "error" },
};

type Session = {
  id: string;
  phone: string;
  profile_name: string | null;
  estado: EstadoAgente;
  ultima_atividade_em: string;
  criado_em: string;
  total_mensagens: number;
};

function useSessions() {
  return useQuery<Session[]>({
    queryKey: ["whatsapp", "sessions"],
    queryFn: async () => {
      const { data, error } = await api.GET("/whatsapp/sessions");
      if (error) throw error;
      return data as Session[];
    },
    refetchInterval: 10_000,
  });
}

function WhatsappSessions() {
  const { data: sessions, isLoading, isError } = useSessions();

  return (
    <div className="p-6 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[--color-text-primary]">WhatsApp</h1>
          <p className="text-sm text-[--color-text-muted] mt-1">
            Sessões ativas — atualiza a cada 10s
          </p>
        </div>
        {sessions && (
          <span className="text-sm text-[--color-text-muted]">
            {sessions.length} sessão{sessions.length !== 1 ? "ões" : ""}
          </span>
        )}
      </header>

      {isError && <p className="text-sm text-[--color-error]">Erro ao carregar sessões.</p>}

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      )}

      {sessions && sessions.length === 0 && (
        <Card>
          <CardContent className="py-10 text-center text-[--color-text-muted] text-sm">
            Nenhuma sessão iniciada ainda.
          </CardContent>
        </Card>
      )}

      {sessions && sessions.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-[--color-border]">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[--color-surface] border-b border-[--color-border]">
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">
                  Telefone
                </th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">Nome</th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">
                  Estado
                </th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">
                  Última atividade
                </th>
                <th className="px-4 py-3 text-right font-medium text-[--color-text-muted]">Msgs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[--color-border]">
              {sessions.map((s) => {
                const badge = ESTADO_BADGE[s.estado] ?? {
                  label: s.estado,
                  variant: "secondary" as const,
                };
                return (
                  <tr
                    key={s.id}
                    className="bg-[--color-surface] hover:bg-[--color-background] transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3 font-mono text-[--color-text-primary]">
                      <Link
                        to="/dashboard/whatsapp/$sessionId"
                        params={{ sessionId: s.id }}
                        className="hover:underline"
                      >
                        {s.phone}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-[--color-text-secondary]">
                      {s.profile_name ?? <span className="text-[--color-text-muted]">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={badge.variant}>{badge.label}</Badge>
                    </td>
                    <td className="px-4 py-3 text-[--color-text-muted]">
                      {formatDateTime(s.ultima_atividade_em)}
                    </td>
                    <td className="px-4 py-3 text-right text-[--color-text-muted]">
                      {s.total_mensagens}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
