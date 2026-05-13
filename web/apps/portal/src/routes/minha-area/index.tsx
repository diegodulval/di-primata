import { setAuthToken } from "@di-mata/api-client";
import { type Account, type Unit, clearToken, formatDate, getToken } from "@di-mata/shared";
import { Field, Input, Select, Skeleton } from "@di-mata/ui";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/minha-area/")({
  beforeLoad: () => {
    if (!getToken()) {
      throw redirect({ to: "/" });
    }
  },
  component: MinhaAreaPage,
});

// ── Tipos locais ──────────────────────────────────────────────────────────────

type Resumo = {
  total_custo: number;
  total_atividades: number;
  por_unidade: { unit_id: string; unit_nome: string; custo: number; atividades: number }[];
};

type Atividade = {
  id: string;
  tipo_evento: string;
  descricao: string;
  custo: number | null;
  capturado_em: string;
  unit_id: string | null;
  unit_nome: string;
};

type LoteGerado = {
  lot_id: string;
  codigo_lote: string;
  qr_hash: string;
  qr_image: string | null;
  gerado_em: string;
  unit_id: string | null;
  unit_nome: string;
  autodeclarado: boolean;
  total_atividades: number;
  total_custo: number;
};

// ── Helpers ───────────────────────────────────────────────────────────────────

async function portalFetch<T>(path: string): Promise<T> {
  const token = getToken();
  const res = await fetch(path, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    clearToken();
    setAuthToken(null);
    window.location.href = "/";
  }
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json() as Promise<T>;
}

async function portalPost<T>(path: string, body: unknown): Promise<T> {
  const token = getToken();
  const res = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    clearToken();
    setAuthToken(null);
    window.location.href = "/";
  }
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json() as Promise<T>;
}

const brl = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const TIPO_LABEL: Record<string, string> = {
  TALHAO: "Talhão",
  VIVEIRO: "Viveiro",
  BAIA: "Baia",
  LINHA_PRODUCAO: "Linha de Produção",
  TEAR: "Tear",
  ATELIE: "Ateliê",
  OUTRO: "Outro",
};

const EVENTO_LABEL: Record<string, string> = {
  ENTRADA_INSUMO: "Entrada de insumo",
  OPERACAO: "Operação",
  CTRL_QUALIDADE: "Controle de qualidade",
  ANOMALIA: "Anomalia",
  MOVIMENTACAO: "Movimentação",
  COLHEITA: "Colheita",
  EXPEDICAO: "Expedição",
};

const today = () => new Date().toISOString().slice(0, 10);

// ── Componente principal ──────────────────────────────────────────────────────

function MinhaAreaPage() {
  const navigate = useNavigate();

  const [account, setAccount] = useState<Account | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [atividades, setAtividades] = useState<Atividade[]>([]);
  const [lotes, setLotes] = useState<LoteGerado[]>([]);
  const [loading, setLoading] = useState(true);

  function loadAtividades() {
    return Promise.all([
      portalFetch<Resumo>("/api/bff/portal/resumo"),
      portalFetch<Atividade[]>("/api/bff/portal/atividades"),
      portalFetch<LoteGerado[]>("/api/bff/portal/lotes"),
    ]).then(([r, a, l]) => {
      setResumo(r);
      setAtividades(a);
      setLotes(l);
    });
  }

  // biome-ignore lint/correctness/useExhaustiveDependencies: loadAtividades only depends on stable setters
  useEffect(() => {
    Promise.all([
      portalFetch<Account>("/api/accounts/me"),
      portalFetch<Unit[]>("/api/units"),
      loadAtividades(),
    ])
      .then(([acc, uns]) => {
        setAccount(acc);
        setUnits(uns);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  function logout() {
    clearToken();
    setAuthToken(null);
    void navigate({ to: "/" });
  }

  return (
    <main className="min-h-screen bg-[--color-background]">
      <header className="bg-[--color-surface] border-b border-[--color-border] px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[--color-primary] flex items-center justify-center">
            <span className="text-[--color-primary-fg] font-bold text-sm">D</span>
          </div>
          <span className="font-semibold text-sm text-[--color-text-primary]">Di Mata</span>
        </div>
        <button
          type="button"
          onClick={logout}
          className="text-xs text-[--color-text-muted] hover:text-[--color-error] transition-colors"
        >
          Sair
        </button>
      </header>

      <div className="max-w-md mx-auto px-4 py-6 space-y-4">
        {/* Conta */}
        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5">
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-24" />
            </div>
          ) : account ? (
            <>
              <h1 className="text-lg font-bold text-[--color-text-primary]">{account.nome}</h1>
              <p className="text-sm text-[--color-text-muted] mt-0.5 capitalize">
                {account.setor_primario}
                {account.whatsapp_phone && (
                  <span className="ml-2 font-mono">{account.whatsapp_phone}</span>
                )}
              </p>
            </>
          ) : null}
        </section>

        {/* Resumo financeiro */}
        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-3">
          <h2 className="text-sm font-semibold text-[--color-text-primary]">
            Custos das atividades
          </h2>
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-8 w-32" />
              <Skeleton className="h-4 w-full" />
            </div>
          ) : (
            <>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-[--color-text-primary]">
                  {brl(resumo?.total_custo ?? 0)}
                </span>
                <span className="text-sm text-[--color-text-muted]">
                  {resumo?.total_atividades ?? 0} atividade
                  {(resumo?.total_atividades ?? 0) !== 1 ? "s" : ""}
                </span>
              </div>
              {(resumo?.por_unidade.length ?? 0) > 0 && (
                <ul className="space-y-1">
                  {resumo?.por_unidade.map((u) => (
                    <li
                      key={u.unit_id}
                      className="flex justify-between text-xs text-[--color-text-muted]"
                    >
                      <span>{u.unit_nome}</span>
                      <span>
                        {brl(u.custo)} · {u.atividades} ativ.
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </section>

        {/* Atividades */}
        <AtividadesSection
          units={units}
          atividades={atividades}
          loading={loading}
          onCreated={loadAtividades}
        />

        {/* QR / fechar safra */}
        <QrSection
          units={units}
          lotes={lotes}
          resumo={resumo}
          loading={loading}
          onGenerated={loadAtividades}
        />

        {/* Rastrear produto */}
        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-3">
          <h2 className="text-sm font-semibold text-[--color-text-primary]">Rastrear produto</h2>
          <TrackInline />
        </section>

        {/* Unidades */}
        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-3">
          <h2 className="text-sm font-semibold text-[--color-text-primary]">Unidades produtivas</h2>
          {loading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <Skeleton key={i} className="h-10 w-full rounded-lg" />
              ))}
            </div>
          ) : units.length === 0 ? (
            <p className="text-sm text-[--color-text-muted]">Nenhuma unidade cadastrada.</p>
          ) : (
            <ul className="space-y-2">
              {units.map((u) => (
                <li
                  key={u.id}
                  className="flex items-center justify-between rounded-lg bg-[--color-background] px-4 py-3"
                >
                  <div>
                    <div className="text-sm font-medium text-[--color-text-primary]">{u.nome}</div>
                    <div className="text-xs text-[--color-text-muted]">
                      {TIPO_LABEL[u.tipo] ?? u.tipo}
                      {u.area_capacidade != null && ` · ${u.area_capacidade} ha`}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}

// ── Seção de atividades ───────────────────────────────────────────────────────

type AtividadesSectionProps = {
  units: Unit[];
  atividades: Atividade[];
  loading: boolean;
  onCreated: () => Promise<void>;
};

function AtividadesSection({ units, atividades, loading, onCreated }: AtividadesSectionProps) {
  const [showForm, setShowForm] = useState(false);

  return (
    <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[--color-text-primary]">Atividades</h2>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="text-xs font-medium text-[--color-primary] hover:underline"
          >
            + Nova atividade
          </button>
        )}
      </div>

      {showForm && (
        <NovaAtividadeForm
          units={units}
          onCancel={() => setShowForm(false)}
          onCreated={async () => {
            setShowForm(false);
            await onCreated();
          }}
        />
      )}

      {loading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : atividades.length === 0 && !showForm ? (
        <p className="text-sm text-[--color-text-muted]">Nenhuma atividade registrada.</p>
      ) : (
        <ul className="space-y-2">
          {atividades.map((a) => (
            <li
              key={a.id}
              className="rounded-lg bg-[--color-background] px-4 py-3 flex items-start justify-between gap-3"
            >
              <div className="min-w-0">
                <div className="text-sm font-medium text-[--color-text-primary] truncate">
                  {a.descricao}
                </div>
                <div className="text-xs text-[--color-text-muted] mt-0.5">
                  {EVENTO_LABEL[a.tipo_evento] ?? a.tipo_evento}
                  {" · "}
                  {a.unit_nome}
                  {" · "}
                  {formatDate(a.capturado_em)}
                </div>
              </div>
              {a.custo != null && (
                <span className="text-sm font-semibold text-[--color-text-primary] whitespace-nowrap">
                  {brl(a.custo)}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// ── Formulário de nova atividade ──────────────────────────────────────────────

type NovaAtividadeFormProps = {
  units: Unit[];
  onCancel: () => void;
  onCreated: () => Promise<void>;
};

function NovaAtividadeForm({ units, onCancel, onCreated }: NovaAtividadeFormProps) {
  const [unitId, setUnitId] = useState(units[0]?.id ?? "");
  const [tipo, setTipo] = useState("OPERACAO");
  const [descricao, setDescricao] = useState("");
  const [custo, setCusto] = useState("");
  const [data, setData] = useState(today());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!descricao.trim()) {
      setError("Descrição obrigatória.");
      return;
    }
    if (!unitId) {
      setError("Selecione uma unidade.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await portalPost("/api/bff/portal/atividades", {
        unit_id: unitId,
        tipo_evento: tipo,
        descricao: descricao.trim(),
        custo: custo ? Number.parseFloat(custo.replace(",", ".")) : null,
        capturado_em: new Date(`${data}T12:00:00`).toISOString(),
      });
      await onCreated();
    } catch {
      setError("Erro ao registrar atividade.");
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 border-t border-[--color-border] pt-4">
      <Field label="Unidade">
        <Select value={unitId} onChange={(e) => setUnitId(e.target.value)}>
          {units.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nome}
            </option>
          ))}
        </Select>
      </Field>

      <Field label="Tipo">
        <Select value={tipo} onChange={(e) => setTipo(e.target.value)}>
          {Object.entries(EVENTO_LABEL).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </Select>
      </Field>

      <Field label="Descrição" error={error && !descricao.trim() ? error : undefined}>
        <Input
          value={descricao}
          onChange={(e) => {
            setDescricao(e.target.value);
            setError("");
          }}
          placeholder="Ex: Aplicação de fertilizante"
        />
      </Field>

      <Field label="Custo (R$)" hint="Opcional">
        <Input
          type="number"
          inputMode="decimal"
          min="0"
          step="0.01"
          value={custo}
          onChange={(e) => setCusto(e.target.value)}
          placeholder="0,00"
        />
      </Field>

      <Field label="Data">
        <Input type="date" value={data} onChange={(e) => setData(e.target.value)} />
      </Field>

      {error && <p className="text-xs text-[--color-error]">{error}</p>}

      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={saving}
          className="flex-1 rounded-lg bg-[--color-primary] px-4 py-2.5 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity disabled:opacity-60"
        >
          {saving ? "Registrando…" : "Registrar"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-[--color-border] px-4 py-2.5 text-sm text-[--color-text-muted] hover:bg-[--color-background] transition-colors"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}

// ── Seção de QR / fechar safra ────────────────────────────────────────────────

type QrSectionProps = {
  units: Unit[];
  lotes: LoteGerado[];
  resumo: Resumo | null;
  loading: boolean;
  onGenerated: () => Promise<void>;
};

function QrSection({ units, lotes, resumo, loading, onGenerated }: QrSectionProps) {
  const activeUnitIds = new Set<string>([
    ...(resumo?.por_unidade.map((u) => u.unit_id) ?? []),
    ...lotes.map((l) => l.unit_id).filter((id): id is string => id !== null),
  ]);
  const activeUnits = units.filter((u) => activeUnitIds.has(u.id));

  if (loading) {
    return (
      <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-3">
        <h2 className="text-sm font-semibold text-[--color-text-primary]">
          Fechar safra e gerar QR
        </h2>
        <Skeleton className="h-28 w-full rounded-xl" />
      </section>
    );
  }

  if (activeUnits.length === 0) return null;

  return (
    <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-4">
      <h2 className="text-sm font-semibold text-[--color-text-primary]">Fechar safra e gerar QR</h2>
      <div className="space-y-4">
        {activeUnits.map((unit) => (
          <UnitQrCard
            key={unit.id}
            unit={unit}
            unitLotes={lotes.filter((l) => l.unit_id === unit.id)}
            unitResumo={resumo?.por_unidade.find((u) => u.unit_id === unit.id) ?? null}
            onGenerated={onGenerated}
          />
        ))}
      </div>
    </section>
  );
}

type UnitQrCardProps = {
  unit: Unit;
  unitLotes: LoteGerado[];
  unitResumo: { unit_id: string; unit_nome: string; custo: number; atividades: number } | null;
  onGenerated: () => Promise<void>;
};

function UnitQrCard({ unit, unitLotes, unitResumo, onGenerated }: UnitQrCardProps) {
  const [autodeclarado, setAutodeclarado] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState("");
  const [newLote, setNewLote] = useState<LoteGerado | null>(null);

  const allLotes = newLote ? [newLote, ...unitLotes] : unitLotes;

  async function handleGenerate() {
    setGenError("");
    setGenerating(true);
    try {
      const lot = await portalPost<LoteGerado>("/api/bff/portal/lotes", {
        unit_id: unit.id,
        autodeclarado: true,
      });
      setNewLote(lot);
      setAutodeclarado(false);
      await onGenerated();
    } catch {
      setGenError("Erro ao gerar QR. Verifique se há atividades registradas.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="rounded-xl border border-[--color-border] p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[--color-text-primary]">{unit.nome}</h3>
        {unitResumo && (
          <span className="text-xs text-[--color-text-muted]">
            {unitResumo.atividades} ativ. · {brl(unitResumo.custo)}
          </span>
        )}
      </div>

      {allLotes.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-[--color-text-muted] uppercase tracking-wide">
            QR codes gerados
          </p>
          {allLotes.map((lot) => (
            <div
              key={lot.lot_id}
              className="flex items-start gap-3 rounded-lg bg-[--color-background] p-3"
            >
              {lot.qr_image && (
                <img
                  src={lot.qr_image}
                  alt={`QR ${lot.codigo_lote}`}
                  className="w-16 h-16 rounded flex-shrink-0"
                />
              )}
              <div className="min-w-0 flex-1 space-y-0.5">
                <p className="text-xs font-mono text-[--color-text-primary] truncate">
                  {lot.codigo_lote}
                </p>
                <p className="text-xs text-[--color-text-muted]">
                  {formatDate(lot.gerado_em)} · {lot.total_atividades} ativ. ·{" "}
                  {brl(lot.total_custo)}
                </p>
                {lot.autodeclarado && (
                  <p className="text-xs text-[--color-primary] font-medium">
                    ✓ Verificado pelo engenheiro
                  </p>
                )}
                <a
                  href={`/p/${lot.qr_hash}`}
                  className="text-xs text-[--color-primary] hover:underline"
                >
                  Ver relatório →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2 border-t border-[--color-border] pt-3">
        <label className="flex items-start gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={autodeclarado}
            onChange={(e) => {
              setAutodeclarado(e.target.checked);
              setGenError("");
            }}
            className="mt-0.5 flex-shrink-0 accent-[--color-primary]"
          />
          <span className="text-xs text-[--color-text-muted] leading-relaxed">
            Declaro que os registros foram verificados pelo engenheiro responsável
          </span>
        </label>

        {genError && <p className="text-xs text-[--color-error]">{genError}</p>}

        <button
          type="button"
          onClick={handleGenerate}
          disabled={generating || !autodeclarado}
          className="w-full rounded-lg bg-[--color-primary] px-4 py-2.5 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity disabled:opacity-40"
        >
          {generating ? "Gerando…" : "Fechar safra e gerar QR code"}
        </button>
      </div>
    </div>
  );
}

// ── Rastrear inline ───────────────────────────────────────────────────────────

function TrackInline() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");

  function handleTrack(e: React.FormEvent) {
    e.preventDefault();
    const hash = code.trim();
    if (hash) void navigate({ to: "/p/$hash", params: { hash } });
  }

  return (
    <form onSubmit={handleTrack} className="flex gap-2">
      <Input
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Código do produto"
        autoCapitalize="none"
        spellCheck={false}
      />
      <button
        type="submit"
        className="rounded-lg bg-[--color-primary] px-4 py-2 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity whitespace-nowrap"
      >
        Buscar
      </button>
    </form>
  );
}
