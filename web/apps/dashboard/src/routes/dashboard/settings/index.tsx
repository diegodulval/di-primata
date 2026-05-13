import { api } from "@di-mata/api-client";
import { Button, Card, CardContent, CardHeader, CardTitle, Field, Input, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/dashboard/settings/")({
  component: Settings,
});

function useAccount() {
  return useQuery({
    queryKey: ["account", "me"],
    queryFn: async () => {
      const { data, error } = await api.GET("/accounts/me");
      if (error) throw error;
      return data;
    },
  });
}

function useUpdateAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { nome?: string; whatsapp_phone?: string | null }) => {
      const { data, error } = await api.PATCH("/accounts/me", { body: payload });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["account", "me"] });
    },
  });
}

function Settings() {
  const { data: account, isLoading } = useAccount();
  const update = useUpdateAccount();

  const [nome, setNome] = useState("");
  const [phone, setPhone] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (account) {
      setNome(account.nome ?? "");
      setPhone(account.whatsapp_phone ?? "");
    }
  }, [account]);

  function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault();
    setSaved(false);
    const payload: { nome?: string; whatsapp_phone?: string | null } = {
      whatsapp_phone: phone.trim() || null,
    };
    if (nome) payload.nome = nome;
    update.mutate(
      payload,
      { onSuccess: () => setSaved(true) },
    );
  }

  return (
    <div className="p-6 max-w-lg space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Configurações</h1>
        <p className="text-sm text-[--color-text-muted] mt-1">Dados da conta e integração WhatsApp</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Informações da conta</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Field label="Nome da propriedade">
                <Input
                  type="text"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="Ex: Fazenda Boa Vista"
                />
              </Field>

              <Field
                label="Telefone WhatsApp"
                hint="Formato internacional, ex: +5511999990000"
              >
                <Input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+5511999990000"
                />
              </Field>

              <div className="flex items-center gap-3 pt-1">
                <Button type="submit" size="md" disabled={update.isPending}>
                  {update.isPending ? "Salvando…" : "Salvar"}
                </Button>
                {saved && !update.isPending && (
                  <span className="text-sm text-[--color-success]">Salvo com sucesso ✓</span>
                )}
                {update.isError && (
                  <span className="text-sm text-[--color-error]">Erro ao salvar.</span>
                )}
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      {account && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informações da conta</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1 text-[--color-text-secondary]">
            <Row label="Documento" value={account.documento} />
            <Row label="E-mail" value={account.email} />
            <Row label="Setor" value={account.setor_primario} />
            <Row label="Plano" value={account.plano} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}


function Row({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div className="flex justify-between">
      <span className="text-[--color-text-muted]">{label}</span>
      <span>{value ?? "—"}</span>
    </div>
  );
}
