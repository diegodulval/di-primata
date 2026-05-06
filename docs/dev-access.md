# Acesso de Desenvolvimento

Credenciais e URLs para o ambiente local. Geradas pelo seed (`make seed`).

> **Atenção:** o estado da API é **in-memory**. Reiniciar a API apaga todos os dados.  
> Execute `make seed` sempre que reiniciar o servidor.

---

## Como subir o ambiente completo

```bash
# Terminal 1 — API
make run

# Terminal 2 — Frontend
make web-dev

# Terminal 3 — Seed (uma vez por sessão)
make seed
```

---

## URLs

| Interface | URL |
|---|---|
| Dashboard (login) | http://localhost:5173/login |
| Portal QR público | http://localhost:5174/p/{hash} |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |

---

## Tenants de teste

### Fazenda Vale do Café
Setor agrícola (CAF) · Plano PREMIUM_AGRO

| Nome | E-mail | Senha | Role |
|---|---|---|---|
| Marcelo Duarte | admin@cafe.dev | dev1234 | ADMIN |
| Sandra Lima | gerente@cafe.dev | dev1234 | ADMIN |
| João Campos | operador@cafe.dev | dev1234 | OPERADOR |

**Ciclos criados pelo seed:**

| Produto | Status | Observação |
|---|---|---|
| Café Arábica Especial — Safra 2026 | `LOTE_GERADO` / publicado | QR escaneável no portal |
| Café Robusta — Safra 2026 | `EM_PRODUCAO` | Ciclo aberto para testes de registro de eventos |

**Portal QR do Café Arábica:**  
O hash é gerado dinamicamente a cada seed. Após `make seed`, o hash é impresso no terminal:
```
Portal QR público (consumidor — sem login):
  http://localhost:5174/p/<hash>
```

---

### Cooperativa Cacau Sul
Setor cacau (CAC) · Plano COOPERATIVA

| Nome | E-mail | Senha | Role |
|---|---|---|---|
| Beatriz Moraes | admin@cacau.dev | dev1234 | ADMIN |
| Rafael Nunes | operador@cacau.dev | dev1234 | OPERADOR |

**Ciclos criados pelo seed:**

| Produto | Status | Observação |
|---|---|---|
| Cacau Fino de Aroma — Safra 2026 | `EM_PRODUCAO` | Evento de fermentação registrado |

---

### Artesanato Tear Vivo
Setor artesanal (ART) · Plano CORE_PLUS

| Nome | E-mail | Senha | Role |
|---|---|---|---|
| Cláudia Mendes | admin@tear.dev | dev1234 | ADMIN |

Sem ciclos — útil para testar **estado vazio** da UI.

---

## Dados criados por tenant

```
Fazenda Vale do Café
├── Unidade: Talhão Norte (TALHAO · -21.7654, -46.5678 · 12,5 ha)
├── Protocolo: Protocolo Café Especial v1 (ref: IN MAPA nº 51/2018)
│   ├── Colheita          [obrigatória]
│   ├── Secagem Natural   [obrigatória]
│   ├── Beneficiamento    [obrigatória]
│   └── Controle QC       [obrigatória]
├── Ciclo 1: Café Arábica Especial · LOTE_GERADO · PUBLICADO
│   ├── Evento: Colheita seletiva — 1800 kg, Brix 22°
│   ├── Evento: Secagem natural — 18 dias
│   └── Evento: Controle QC — score SCA 86
└── Ciclo 2: Café Robusta · EM_PRODUCAO
    └── (aguardando eventos)

Cooperativa Cacau Sul
├── Unidade: Linha de Processamento 1 (LINHA_PRODUCAO · 500 m²)
├── Protocolo: Protocolo Cacau Fino v1 (ref: Decreto 7.623/2011)
│   ├── Fermentação       [obrigatória]
│   ├── Secagem ao Sol    [obrigatória]
│   └── Classificação     [obrigatória]
└── Ciclo: Cacau Fino de Aroma · EM_PRODUCAO
    └── Evento: Fermentação 120h, pH 4.2, temp. máx. 48°C

Artesanato Tear Vivo
├── Unidade: Tear Principal (TEAR)
├── Protocolo: Protocolo Tear Manual v1
│   ├── Tingimento Natural [obrigatória]
│   └── Tecelagem         [obrigatória]
└── (sem ciclos)
```

---

## Casos de uso cobertos pelo seed

| Caso | Onde testar |
|---|---|
| Login e navegação autenticada | Dashboard · admin@cafe.dev |
| Perfil operador (permissões reduzidas) | Dashboard · operador@cafe.dev |
| Tenant diferente (isolamento) | Dashboard · admin@cacau.dev |
| Portal QR do consumidor | http://localhost:5174/p/{hash} |
| Estado vazio (onboarding UI) | Dashboard · admin@tear.dev |
| Ciclo em andamento | Dashboard · admin@cafe.dev → Café Robusta |
| API indisponível | Parar `make run` e acessar o dashboard |

---

## Re-seeding

O seed é idempotente no sentido de que pode ser re-executado, mas como o estado é in-memory, reiniciar a API já limpa tudo.

```bash
# Para resseedear sem reiniciar a API, não é possível — dados vivem na memória do processo.
# Reinicie a API e execute o seed novamente:
make run   # Ctrl+C no terminal da API e suba novamente
make seed
```
