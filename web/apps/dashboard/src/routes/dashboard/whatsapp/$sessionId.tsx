import { api } from "@di-mata/api-client";
import { formatDateTime } from "@di-mata/shared";
import type { EstadoAgente } from "@di-mata/shared";
import { Badge, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/whatsapp/$sessionId")({
  component: SessionDetail,
});

type Session = {
  id: string;
  phone: string;
  profile_name: string | null;
  estado: EstadoAgente;
  ultima_atividade_em: string;
  criado_em: string;
};

type Message = {
  id: string;
  sessao_id: string;
  sid: string;
  direcao: "INBOUND" | "OUTBOUND";
  corpo: string;
  num_midia: number;
  midia_urls: string[];
  criado_em: string;
};

const ESTADO_BADGE: Record<
  EstadoAgente,
  { label: string; variant: "default" | "secondary" | "outline" | "warning" | "error" }
> = {
  OCIOSO: { label: "Ocioso", variant: "secondary" },
  ESCUTANDO: { label: "Escutando", variant: "outline" },
  PROCESSANDO: { label: "Processando", variant: "warning" },
  AGUARD_CONFIRM: { label: "Aguard. confirm", variant: "default" },
  SINCRONIZANDO: { label: "Sincronizando", variant: "default" },
  OFFLINE: { label: "Offline", variant: "error" },
};

function useSession(sessionId: string) {
  return useQuery<Session>({
    queryKey: ["whatsapp", "sessions", sessionId],
    queryFn: async () => {
      const { data, error } = await api.GET("/whatsapp/sessions/{session_id}", {
        params: { path: { session_id: sessionId } },
      });
      if (error) throw error;
      return data as Session;
    },
  });
}

function useMessages(sessionId: string) {
  return useQuery<Message[]>({
    queryKey: ["whatsapp", "sessions", sessionId, "messages"],
    queryFn: async () => {
      const { data, error } = await api.GET("/whatsapp/sessions/{session_id}/messages", {
        params: { path: { session_id: sessionId } },
      });
      if (error) throw error;
      return data as Message[];
    },
    refetchInterval: 5_000,
  });
}

function Bubble({ msg }: { msg: Message }) {
  const isInbound = msg.direcao === "INBOUND";
  return (
    <div className={`flex ${isInbound ? "justify-start" : "justify-end"}`}>
      <div
        className={[
          "max-w-[70%] rounded-2xl px-4 py-2.5 text-sm",
          isInbound
            ? "bg-[--color-background] border border-[--color-border] text-[--color-text-primary] rounded-tl-sm"
            : "bg-[--color-primary] text-[--color-primary-fg] rounded-tr-sm",
        ].join(" ")}
      >
        <p className="whitespace-pre-wrap break-words">{msg.corpo}</p>
        {msg.midia_urls.map((url) => (
          <a
            key={url}
            href={url}
            target="_blank"
            rel="noreferrer"
            className="block mt-1 text-xs underline opacity-70"
          >
            📎 mídia
          </a>
        ))}
        <p
          className={[
            "text-[10px] mt-1",
            isInbound ? "text-[--color-text-muted]" : "opacity-70 text-right",
          ].join(" ")}
        >
          {formatDateTime(msg.criado_em)}
        </p>
      </div>
    </div>
  );
}

function SessionDetail() {
  const { sessionId } = Route.useParams();
  const { data: session, isLoading: loadingSession } = useSession(sessionId);
  const { data: messages, isLoading: loadingMsgs } = useMessages(sessionId);

  const badge = session
    ? (ESTADO_BADGE[session.estado] ?? { label: session.estado, variant: "secondary" as const })
    : null;

  return (
    <div className="p-6 flex flex-col gap-4 h-full">
      {/* Cabeçalho */}
      <div className="flex items-center gap-3">
        <Link
          to="/dashboard/whatsapp"
          className="text-sm text-[--color-text-muted] hover:text-[--color-text-primary] transition-colors"
        >
          ← Sessões
        </Link>

        {loadingSession && <Skeleton className="h-5 w-48" />}

        {session && (
          <div className="flex items-center gap-2 ml-1">
            <span className="font-mono font-medium text-[--color-text-primary]">
              {session.phone}
            </span>
            {session.profile_name && (
              <span className="text-sm text-[--color-text-muted]">· {session.profile_name}</span>
            )}
            {badge && <Badge variant={badge.variant}>{badge.label}</Badge>}
          </div>
        )}
      </div>

      {session && (
        <p className="text-xs text-[--color-text-muted]">
          Sessão iniciada em {formatDateTime(session.criado_em)} · última atividade{" "}
          {formatDateTime(session.ultima_atividade_em)}
        </p>
      )}

      {/* Thread de mensagens */}
      <div className="flex-1 overflow-y-auto rounded-lg border border-[--color-border] bg-[--color-surface] p-4 space-y-3 min-h-[400px]">
        {loadingMsgs && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton
                key={i}
                className={`h-12 w-2/3 rounded-2xl ${i % 2 === 0 ? "ml-auto" : ""}`}
              />
            ))}
          </div>
        )}

        {messages && messages.length === 0 && (
          <p className="text-center text-sm text-[--color-text-muted] py-8">
            Nenhuma mensagem nesta sessão.
          </p>
        )}

        {messages?.map((msg) => <Bubble key={msg.id} msg={msg} />)}
      </div>

      <p className="text-xs text-[--color-text-muted] text-right">
        Atualiza automaticamente a cada 5s
      </p>
    </div>
  );
}
