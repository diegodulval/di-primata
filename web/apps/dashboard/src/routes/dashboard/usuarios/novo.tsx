import type { SelectOption } from "@di-mata/shared";
import { Card, CardContent, Field, Input, Select, StepIndicator } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/dashboard/usuarios/novo")({
  component: NovoUsuarioPage,
});

// ── Tipos ─────────────────────────────────────────────────────────────────────

type UnitDraft = { nome: string; tipo: string; area_capacidade: string };

type FormState = {
  // Step 1 — usuário
  nome: string;
  email: string;
  senha: string;
  confirmar_senha: string;
  // Step 2 — perfil
  role: string;
  setor_primario: string;
  whatsapp_phone: string;
  // Step 3 — organização (apenas PRODUTOR)
  nome_conta: string;
  documento: string;
  unidades: UnitDraft[];
};

const INITIAL_FORM: FormState = {
  nome: "",
  email: "",
  senha: "",
  confirmar_senha: "",
  role: "",
  setor_primario: "",
  whatsapp_phone: "",
  nome_conta: "",
  documento: "",
  unidades: [],
};

// ── Constantes ────────────────────────────────────────────────────────────────

const ROLES = [
  {
    value: "PRODUTOR",
    label: "Produtor",
    desc: "Acesso ao portal do produtor: resumo financeiro, rastreabilidade e QR codes.",
  },
  {
    value: "OPERADOR",
    label: "Operador",
    desc: "Acesso operacional ao dashboard para registro de eventos e ciclos.",
  },
  {
    value: "CONSULTOR",
    label: "Consultor",
    desc: "Acesso de leitura para análise e auditoria da produção.",
  },
  {
    value: "ADMIN",
    label: "Administrador",
    desc: "Acesso completo à plataforma, incluindo gestão de usuários.",
  },
];

const INDUSTRIAL_KEYS = new Set([
  "industrial",
  "industria",
  "manufatura",
  "fabrica",
  "textil",
  "metalurgica",
  "alimenticia",
  "quimica",
  "moveleira",
]);

function detectDomain(setor: string) {
  const n = setor.toLowerCase();
  for (const k of INDUSTRIAL_KEYS) if (n.includes(k)) return "industrial";
  return "rural";
}

const RURAL_UNIT_TYPES: SelectOption[] = [
  { value: "TALHAO", label: "Talhão" },
  { value: "VIVEIRO", label: "Viveiro" },
  { value: "BAIA", label: "Baia" },
];
const INDUSTRIAL_UNIT_TYPES: SelectOption[] = [
  { value: "LINHA_PRODUCAO", label: "Linha de Produção" },
  { value: "TEAR", label: "Tear" },
  { value: "ATELIE", label: "Ateliê" },
  { value: "OUTRO", label: "Outro" },
];

// ── Fetchers ──────────────────────────────────────────────────────────────────

function useSetorOptions() {
  return useQuery<SelectOption[]>({
    queryKey: ["bff", "setor-options"],
    queryFn: async () => {
      const token = sessionStorage.getItem("access_token");
      const res = await fetch("/api/bff/setor-options", {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: Infinity,
  });
}

// ── Componentes de apoio ──────────────────────────────────────────────────────

// ── Steps ─────────────────────────────────────────────────────────────────────

function Step1({
  form,
  onChange,
  errors,
}: {
  form: FormState;
  onChange: (patch: Partial<FormState>) => void;
  errors: Partial<Record<keyof FormState, string>>;
}) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-[--color-text-muted]">
        Dados de identificação e acesso à plataforma.
      </p>

      <Field label="Nome completo" error={errors.nome}>
        <Input
          value={form.nome}
          onChange={(e) => onChange({ nome: e.target.value })}
          placeholder="Nome do usuário"
          autoFocus
        />
      </Field>

      <Field label="E-mail" error={errors.email}>
        <Input
          value={form.email}
          onChange={(e) => onChange({ email: e.target.value })}
          placeholder="email@exemplo.com"
          type="email"
        />
      </Field>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Senha" error={errors.senha}>
          <Input
            value={form.senha}
            onChange={(e) => onChange({ senha: e.target.value })}
            type="password"
            placeholder="Mínimo 6 caracteres"
          />
        </Field>
        <Field label="Confirmar senha" error={errors.confirmar_senha}>
          <Input
            value={form.confirmar_senha}
            onChange={(e) => onChange({ confirmar_senha: e.target.value })}
            type="password"
            placeholder="Repita a senha"
          />
        </Field>
      </div>
    </div>
  );
}

function Step2({
  form,
  onChange,
  errors,
  setorOptions,
}: {
  form: FormState;
  onChange: (patch: Partial<FormState>) => void;
  errors: Partial<Record<keyof FormState, string>>;
  setorOptions: SelectOption[];
}) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-[--color-text-muted]">
        Defina o perfil de acesso. Produtores recebem acesso ao portal.
      </p>

      <Field label="Perfil de acesso" error={errors.role}>
        <div className="space-y-2">
          {ROLES.map((r) => (
            <label
              key={r.value}
              className={[
                "flex items-start gap-3 rounded-lg border px-4 py-3 cursor-pointer transition-colors",
                form.role === r.value
                  ? "border-[--color-primary] bg-[--color-primary]/5"
                  : "border-[--color-border] hover:bg-[--color-background]",
              ].join(" ")}
            >
              <input
                type="radio"
                name="role"
                value={r.value}
                checked={form.role === r.value}
                onChange={() => onChange({ role: r.value })}
                className="mt-0.5 accent-[--color-primary]"
              />
              <div>
                <div className="text-sm font-medium text-[--color-text-primary]">{r.label}</div>
                <div className="text-xs text-[--color-text-muted] mt-0.5">{r.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </Field>

      {form.role === "PRODUTOR" && (
        <>
          <Field label="Setor de atuação" error={errors.setor_primario}>
            <Select
              value={form.setor_primario}
              onChange={(e) => onChange({ setor_primario: e.target.value })}
            >
              <option value="">Selecione o setor...</option>
              {setorOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </Select>
            {form.setor_primario && (
              <p className="text-xs text-[--color-text-muted] mt-1">
                Domínio:{" "}
                <span className="font-medium">
                  {detectDomain(form.setor_primario) === "rural" ? "Rural" : "Industrial"}
                </span>
              </p>
            )}
          </Field>

          <Field label="WhatsApp (opcional)">
            <Input
              value={form.whatsapp_phone}
              onChange={(e) => onChange({ whatsapp_phone: e.target.value })}
              placeholder="+55 11 99999-0000"
              type="tel"
            />
          </Field>
        </>
      )}
    </div>
  );
}

function Step3({
  form,
  onChange,
  errors,
}: {
  form: FormState;
  onChange: (patch: Partial<FormState>) => void;
  errors: Partial<Record<keyof FormState, string>>;
}) {
  const unitTypes =
    detectDomain(form.setor_primario) === "rural" ? RURAL_UNIT_TYPES : INDUSTRIAL_UNIT_TYPES;
  const defaultTipo = unitTypes[0]?.value ?? "TALHAO";
  const unitLabel = detectDomain(form.setor_primario) === "rural" ? "talhão" : "unidade";

  function addUnit() {
    onChange({
      unidades: [...form.unidades, { nome: "", tipo: defaultTipo, area_capacidade: "" }],
    });
  }

  function removeUnit(idx: number) {
    onChange({ unidades: form.unidades.filter((_, i) => i !== idx) });
  }

  function updateUnit(idx: number, patch: Partial<UnitDraft>) {
    onChange({
      unidades: form.unidades.map((u, i) => (i === idx ? { ...u, ...patch } : u)),
    });
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-[--color-text-muted]">
        Dados da organização vinculada ao produtor no portal.
      </p>

      <Field label="Nome da organização / propriedade" error={errors.nome_conta}>
        <Input
          value={form.nome_conta}
          onChange={(e) => onChange({ nome_conta: e.target.value })}
          placeholder="Ex: Fazenda São João"
          autoFocus
        />
      </Field>

      <Field label="Documento (CPF / CNPJ)" error={errors.documento}>
        <Input
          value={form.documento}
          onChange={(e) => onChange({ documento: e.target.value })}
          placeholder="000.000.000-00 ou 00.000.000/0001-00"
        />
      </Field>

      <div className="pt-2">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-[--color-text-secondary]">
            Unidades iniciais (opcional)
          </span>
          <button
            type="button"
            onClick={addUnit}
            className="text-sm text-[--color-primary] hover:underline"
          >
            + Adicionar {unitLabel}
          </button>
        </div>

        {form.unidades.length === 0 && (
          <div className="rounded-lg border border-dashed border-[--color-border] py-6 text-center text-sm text-[--color-text-muted]">
            Nenhuma unidade adicionada. Você pode cadastrar depois.
          </div>
        )}

        <div className="space-y-3">
          {form.unidades.map((u, i) => (
            <div
              key={i}
              className="flex items-end gap-3 p-3 rounded-lg border border-[--color-border] bg-[--color-surface]"
            >
              <div className="flex-1 space-y-1">
                <label className="text-xs font-medium text-[--color-text-muted]">Nome</label>
                <Input
                  value={u.nome}
                  onChange={(e) => updateUnit(i, { nome: e.target.value })}
                  placeholder={`Nome do ${unitLabel}`}
                />
              </div>
              <div className="w-44 space-y-1">
                <label className="text-xs font-medium text-[--color-text-muted]">Tipo</label>
                <Select value={u.tipo} onChange={(e) => updateUnit(i, { tipo: e.target.value })}>
                  {unitTypes.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="w-28 space-y-1">
                <label className="text-xs font-medium text-[--color-text-muted]">Área (ha)</label>
                <Input
                  value={u.area_capacidade}
                  onChange={(e) => updateUnit(i, { area_capacidade: e.target.value })}
                  placeholder="0,0"
                  type="number"
                  min="0"
                  step="0.1"
                />
              </div>
              <button
                type="button"
                onClick={() => removeUnit(i)}
                className="mb-0.5 text-[--color-text-muted] hover:text-[--color-error] transition-colors text-lg leading-none"
                title="Remover"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Validação ─────────────────────────────────────────────────────────────────

function validate(step: number, form: FormState): Partial<Record<keyof FormState, string>> {
  const errs: Partial<Record<keyof FormState, string>> = {};
  if (step === 0) {
    if (!form.nome.trim()) errs.nome = "Nome é obrigatório";
    if (!form.email.trim()) errs.email = "E-mail é obrigatório";
    if (form.senha.length < 6) errs.senha = "Mínimo 6 caracteres";
    if (form.senha !== form.confirmar_senha) errs.confirmar_senha = "Senhas não coincidem";
  }
  if (step === 1) {
    if (!form.role) errs.role = "Selecione um perfil";
    if (form.role === "PRODUTOR" && !form.setor_primario) errs.setor_primario = "Selecione o setor";
  }
  if (step === 2) {
    if (!form.nome_conta.trim()) errs.nome_conta = "Nome da organização é obrigatório";
    if (!form.documento.trim()) errs.documento = "Documento é obrigatório";
  }
  return errs;
}

// ── Página principal ──────────────────────────────────────────────────────────

function NovoUsuarioPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: setorOptions = [] } = useSetorOptions();

  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [apiError, setApiError] = useState<string | null>(null);

  // Produtor tem 3 steps; demais roles têm 2
  const totalSteps = form.role === "PRODUTOR" ? 3 : 2;
  const STEP_TITLES = ["Dados do usuário", "Perfil de acesso", "Organização"];

  function onChange(patch: Partial<FormState>) {
    setForm((f) => ({ ...f, ...patch }));
    setErrors({});
    setApiError(null);
  }

  const mutation = useMutation({
    mutationFn: async () => {
      const token = sessionStorage.getItem("access_token");
      const payload: Record<string, unknown> = {
        nome: form.nome,
        email: form.email,
        senha: form.senha,
        role: form.role,
      };

      if (form.role === "PRODUTOR") {
        payload.setor_primario = form.setor_primario;
        payload.whatsapp_phone = form.whatsapp_phone || null;
        payload.nome_conta = form.nome_conta;
        payload.documento = form.documento;
        payload.unidades = form.unidades
          .filter((u) => u.nome.trim())
          .map((u) => ({
            nome: u.nome,
            tipo: u.tipo,
            area_capacidade: u.area_capacidade ? parseFloat(u.area_capacidade) : null,
          }));
      }

      const res = await fetch("/api/bff/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Erro ao cadastrar");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bff", "users"] });
      queryClient.invalidateQueries({ queryKey: ["bff", "stats"] });
      void navigate({ to: "/dashboard/usuarios" });
    },
    onError: (err: Error) => {
      setApiError(err.message);
    },
  });

  function next() {
    const errs = validate(step, form);
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setStep((s) => s + 1);
  }

  function back() {
    setStep((s) => s - 1);
    setErrors({});
  }

  function submit() {
    const errs = validate(step, form);
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    mutation.mutate();
  }

  const isLastStep = step === totalSteps - 1;

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to="/dashboard/usuarios"
          className="text-sm text-[--color-text-muted] hover:text-[--color-text-primary] transition-colors"
        >
          ← Usuários
        </Link>
        <span className="text-[--color-text-muted]">/</span>
        <span className="text-sm text-[--color-text-primary] font-medium">Novo usuário</span>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          <div className="flex items-center justify-between">
            <StepIndicator current={step} total={totalSteps} />
            <span className="text-sm text-[--color-text-muted]">{STEP_TITLES[step]}</span>
          </div>

          <div className="border-t border-[--color-border]" />

          {step === 0 && <Step1 form={form} onChange={onChange} errors={errors} />}
          {step === 1 && (
            <Step2 form={form} onChange={onChange} errors={errors} setorOptions={setorOptions} />
          )}
          {step === 2 && <Step3 form={form} onChange={onChange} errors={errors} />}

          {apiError && (
            <p className="text-sm text-[--color-error] bg-[--color-error]/10 rounded-md px-3 py-2">
              {apiError}
            </p>
          )}

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={back}
              disabled={step === 0}
              className="px-4 py-2 text-sm text-[--color-text-secondary] hover:text-[--color-text-primary] disabled:opacity-0 transition-colors"
            >
              ← Voltar
            </button>

            {!isLastStep ? (
              <button
                type="button"
                onClick={next}
                className="px-6 py-2 rounded-md bg-[--color-primary] text-[--color-primary-fg] text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Próximo →
              </button>
            ) : (
              <button
                type="button"
                onClick={submit}
                disabled={mutation.isPending}
                className="px-6 py-2 rounded-md bg-[--color-primary] text-[--color-primary-fg] text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
              >
                {mutation.isPending ? "Cadastrando..." : "Cadastrar usuário"}
              </button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
