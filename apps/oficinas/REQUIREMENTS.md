# Requisitos — DiAuto · Sistema de Gestão de Oficina Mecânica

> `apps/oficinas` — Backend FastAPI + Frontend React (web/apps/oficinas)
> Última atualização: 2026-05-23

---

## Visão Geral

SaaS multi-tenant para gestão de oficinas mecânicas e auto peças. Cada oficina é um **tenant** isolado por RLS no PostgreSQL. Veículos são entidades **globais** (cross-tenant) — histórico persiste mesmo quando o carro troca de dono ou de oficina.

---

## 1. IAM — Identidade e Controle de Acesso

### Perfis
| Perfil | Identificador de Login | Acesso |
|---|---|---|
| `ADMIN` | e-mail | Tudo |
| `ATENDENTE` | e-mail | Leitura + operação, sem admin |
| `MECANICO` | número WhatsApp | OS próprias + agente |

### Endpoints
| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/auth/login` | — | Autenticação por e-mail ou WhatsApp + senha; retorna JWT |
| `GET` | `/usuarios/me` | AUTENTICADO | Perfil próprio |
| `PATCH` | `/usuarios/me/senha` | AUTENTICADO | Trocar própria senha |
| `GET` | `/usuarios/ativos` | AUTENTICADO | Lista simplificada (id, nome, perfil) |
| `POST` | `/usuarios` | ADMIN | Criar usuário do tenant |
| `GET` | `/usuarios` | ADMIN | Listar com paginação |
| `GET` | `/usuarios/{id}` | ADMIN | Detalhar |
| `PATCH` | `/usuarios/{id}` | ADMIN | Atualizar (nome, perfil, WhatsApp, ativo) |
| `DELETE` | `/usuarios/{id}` | ADMIN | Soft-delete (marca `ativo=false`) |

### Regras
- MECANICO **obriga** `numero_whatsapp` e **não usa** e-mail
- ADMIN/ATENDENTE **obrigam** e-mail e **não usam** WhatsApp
- `numero_whatsapp` é **único global** (cross-tenant)
- JWT carrega: `sub` (id), `tenant_id`, `perfil`

---

## 2. Cadastros — Clientes e Veículos

### 2.1 Clientes

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/clientes` | ATENDENTE+ | Criar cliente |
| `GET` | `/clientes` | ATENDENTE+ | Listar com filtros |
| `GET` | `/clientes/{id}` | ATENDENTE+ | Detalhar |
| `PATCH` | `/clientes/{id}` | ATENDENTE+ | Atualizar |
| `POST` | `/clientes/importar` | ADMIN | Upload XLSX de clientes |
| `POST` | `/clientes/importar-veiculos-json` | ADMIN | Upload JSON (formato concorrente) com vínculos cliente-veículo |

**Filtros de listagem:** `?q=` (nome, CPF, celular, apelido, **placa do veículo**), `?tipo_pessoa=`, `?ativo=`, `?uf=`, `?page=`, `?page_size=`

**Campos do cliente:** nome, tipo_pessoa (Fisica/Juridica), cpf_cnpj, rg, apelido, data_nascimento, sexo, telefone, celular, email, cep, endereco, cidade, uf, inscricao_estadual, consumidor_final, indicador_ie (padrão `9`), observacoes, ativo

### 2.2 Vínculo Cliente-Veículo

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `GET` | `/clientes/{id}/veiculos` | ATENDENTE+ | Veículos vinculados (histórico de posse) |
| `POST` | `/clientes/{id}/veiculos` | ATENDENTE+ | Vincular veículo |
| `DELETE` | `/clientes/{id}/veiculos/{veiculo_id}` | ATENDENTE+ | Desassociar (marca `data_fim`, `ativo=false`) |

**Regras de posse:**
- `data_fim = NULL` significa dono atual neste tenant
- Desassociar **não deleta** — mantém histórico de posse
- Vincular novo dono: fecha vínculo anterior automaticamente

### 2.3 Importação JSON de Veículos (Migração de Concorrente)

Fluxo de match em 3 camadas (só usa match único em ambas as bases):
1. **CPF/CNPJ** — correspondência exata
2. **Telefone** — somente dígitos, unique nos dois datasets
3. **Nome normalizado** — sem acentos, unique nos dois datasets

Após match: upsert global do veículo + criação do vínculo cliente-veículo. Enriquece campos nulos do cliente (apelido, cidade, uf, telefone).

---

## 3. Veículo Global

Entidade cross-tenant. Sem RLS. Histórico append-only.

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/veiculos` | ATENDENTE+ | Upsert por placa (idempotente) |
| `GET` | `/veiculos/{placa}` | AUTENTICADO | Buscar + histórico público opt-in |
| `GET` | `/veiculos/{placa}/cliente-atual` | ATENDENTE+ | Dono ativo no tenant |
| `GET` | `/veiculos/{placa}/historico` | ATENDENTE+ | OS fechadas do veículo neste tenant |

**Campos do veículo:** placa (unique global), chassi, marca, modelo, ano_fab, ano_mod, cor, tipo (carro/moto/caminhao/van)

**Histórico público:** gerado no fechamento da OS quando `compartilhar_historico=true`. Contém `resumo_publico` (texto livre) + data + km. Visível a qualquer tenant que buscar a placa.

**Histórico privado (`detalhe_privado`):** gerado automaticamente no fechamento, contém serviços, peças, quantidades, preços e totais. Visível apenas ao tenant dono da OS.

---

## 4. Estoque

### 4.1 Produtos

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/produtos` | ADMIN | Criar produto |
| `GET` | `/produtos` | ATENDENTE+ | Listar ativos com paginação (`?q=`, `?page=`, `?page_size=50`) |
| `GET` | `/produtos/marcas` | ATENDENTE+ | Lista de marcas distintas |
| `GET` | `/produtos/{id}` | ATENDENTE+ | Detalhar |
| `PATCH` | `/produtos/{id}` | ADMIN | Atualizar |
| `GET` | `/produtos/{id}/movimentacoes` | ATENDENTE+ | Histórico append-only de estoque |
| `POST` | `/produtos/importar` | ADMIN | Upload XLSX |

**Campos do produto:** codigo (unique por tenant), descricao, ncm, marca, localizacao, ean, ref_fabricante, unidade_medida, preco_custo, preco_venda, estoque_atual, estoque_minimo, estoque_maximo, peso_liquido, peso_bruto, origem_mercadoria, observacoes, ativo

**Movimentações (append-only):** ENTRADA · SAIDA · RESERVA · LIBERACAO

### 4.2 Fornecedores

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/fornecedores` | ADMIN | Criar |
| `GET` | `/fornecedores` | ATENDENTE+ | Listar (`?q=`, `?ativo=`, `?tipo_pessoa=`) |
| `GET` | `/fornecedores/{id}` | ATENDENTE+ | Detalhar |
| `PATCH` | `/fornecedores/{id}` | ADMIN | Atualizar |
| `GET` | `/fornecedores/{id}/produtos` | ATENDENTE+ | Produtos mapeados com código do fornecedor |
| `POST` | `/fornecedores/importar` | ADMIN | Upload XLSX |

### 4.3 Entrada de NF-e (Rascunho + Confirmação)

Fluxo completo descrito na [seção 9 — NF-e](#9-entrada-de-nf-e-requisito-detalhado).

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/entradas/xml` | ADMIN | Upload XML → cria rascunho com itens |
| `GET` | `/entradas/rascunhos` | ATENDENTE+ | Listar rascunhos |
| `GET` | `/entradas/rascunhos/{id}` | ATENDENTE+ | Detalhar rascunho + itens |
| `PATCH` | `/entradas/rascunhos/{id}/itens/{item_id}` | ADMIN | Vincular item a produto ou criar novo |
| `POST` | `/entradas/rascunhos/{id}/confirmar` | ADMIN | Confirmar → gera EntradaNfe + ENTRADA no estoque |
| `DELETE` | `/entradas/rascunhos/{id}` | ADMIN | Cancelar rascunho |
| `GET` | `/entradas/{id}` | ATENDENTE+ | Detalhar entrada confirmada |
| `PATCH` | `/entradas/{id}` | ADMIN | Salvar `data_entrada` → status PROCESSADA |

**Regras de movimentação de estoque:**
- Estoque só é atualizado na **confirmação** — nunca no rascunho
- Cancelar rascunho **não afeta** o estoque
- NF-e já importada → `NFeJaImportada` 409

---

## 5. Ordens de Serviço

### Ciclo de Vida
```
ABERTA → EM_EXECUCAO ↔ AGUARDANDO_PECA
                              ↓
                           FECHADA
ABERTA | EM_EXECUCAO | AGUARDANDO_PECA → CANCELADA
```

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/os` | AUTENTICADO | Abrir OS |
| `GET` | `/os` | AUTENTICADO | Listar (`?status_os=`, `?mecanico_id=`, `?placa=`) |
| `GET` | `/os/{id}` | AUTENTICADO | Detalhar (enriquece cliente_nome, veiculo_placa) |
| `POST` | `/os/{id}/itens` | AUTENTICADO | Adicionar item (peça ou serviço) |
| `GET` | `/os/{id}/itens` | AUTENTICADO | Listar itens |
| `DELETE` | `/os/{id}/itens/{item_id}` | AUTENTICADO | Remover item |
| `PATCH` | `/os/{id}/status` | AUTENTICADO | Avançar status |
| `POST` | `/os/{id}/fechar` | ATENDENTE+ | Fechar OS |
| `POST` | `/os/{id}/cancelar` | ATENDENTE+ | Cancelar OS |
| `POST` | `/os/{id}/apontamentos` | AUTENTICADO | Lançar apontamento de horas |
| `GET` | `/os/{id}/apontamentos` | AUTENTICADO | Listar apontamentos |
| `DELETE` | `/os/{id}/apontamentos/{apt_id}` | AUTENTICADO | Remover apontamento |

### Regras de Estoque
| Evento | Movimentação |
|---|---|
| Adicionar peça na OS | `RESERVA` — reduz saldo disponível |
| Remover peça da OS | `LIBERACAO` — devolve saldo |
| Fechar OS | `SAIDA` — converte RESERVA em saída definitiva |
| Cancelar OS | `LIBERACAO` — libera todas as reservas |

### Fechamento da OS
- `compartilhar_historico = false` (padrão) — apenas `detalhe_privado` é populado
- `compartilhar_historico = true` — `resumo_publico` (texto livre) gravado em `global.historico_veiculo`
- `detalhe_privado` é sempre gerado: lista serviços, peças, quantidades, preços e totais

### Apontamentos de Horas
- Vinculados a um item da OS (opcional) ou descrição livre
- Campos: funcionário, item_os (opcional), descrição, duração (horas + minutos), data

---

## 6. Vendas (PDV Balcão)

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/vendas` | ATENDENTE+ | Registrar venda com itens (gera `SAIDA` no estoque) |
| `GET` | `/vendas` | ATENDENTE+ | Listar vendas do tenant |
| `GET` | `/vendas/{id}` | ATENDENTE+ | Detalhar com itens |

- Cliente é opcional (venda balcão anônima)
- Origem: `BALCAO` (direta) ou `OS` (gerada no fechamento)
- Status: `CONCLUIDA` (imediato)
- Cada item gera `movimentacao_estoque.tipo_mov = SAIDA`

---

## 7. Movimentos (Dashboard Unificado)

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `GET` | `/movimentos` | AUTENTICADO | UNION de OS + Vendas com filtros unificados |

**Filtros:** `?tipo=OS|VENDA`, `?status=`, `?q=` (número ou nome do cliente), `?data_inicial=`, `?data_final=`

**Retorno:** id, tipo, numero, cliente_nome, placa, valor, status, criado_em, fechada_em — ordenado por `criado_em DESC`

---

## 8. Frontend — Telas Implementadas

### Layout e Navegação
- Sidebar com navegação entre módulos
- Autenticação JWT via sessionStorage; beforeLoad redireciona para `/login`
- Token Bearer injetado automaticamente em todas as requisições

### Telas

| Rota | Tela | Funcionalidades |
|---|---|---|
| `/app/` | Home | KPI cards: total de clientes, produtos, fornecedores |
| `/app/clientes` | Clientes | Tabela paginada; filtros q/tipo/ativo/uf/placa; criar inline; importar XLSX; importar veículos JSON; "Nova OS" por linha; editar modal |
| `/app/clientes/{id}` | Detalhe do cliente | Dados completos em 4 seções (identificação, contato, endereço, fiscal); veículos vinculados com placa clicável → página do veículo; vincular/desassociar veículo |
| `/app/veiculos` | Veículos | Busca global por placa; upsert inline; listagem paginada |
| `/app/veiculos/{placa}` | Detalhe do veículo | Card do veículo; timeline de OS do tenant (expansível por itens); histórico público de outras oficinas; botão "Nova OS" |
| `/app/os` | Ordens de Serviço | Tabela com badges de status coloridos; filtros por status e placa; "Nova OS" |
| `/app/os/nova` | Nova OS | Busca de veículo por placa (ou cria inline); pré-seleção automática de cliente (dono do veículo); pré-preenchimento via `?cliente_id=` (com picker se múltiplos veículos) ou `?placa=`; km; descrição do problema |
| `/app/os/{id}` | Detalhe da OS | Status com badges; adicionar/remover itens (peça com busca de produto ou serviço livre); totalizadores; fechar (com opt-in de histórico público); cancelar; apontamentos de horas; placa clicável → página do veículo |
| `/app/estoque` | Estoque | Tabela de produtos paginada; criar inline; importar XLSX |
| `/app/estoque/entradas` | Entradas NF-e | Upload XML; tabela de rascunhos com status e pendentes |
| `/app/estoque/nfe-revisao.{id}` | Revisão NF-e | Tabela de itens com status; vincular a produto existente (busca em tempo real) ou criar novo; botão confirmar |
| `/app/estoque/entrada/{id}` | Detalhe da entrada | Dados da nota; data de entrada editável por nota e por item |
| `/app/fornecedores` | Fornecedores | CRUD; filtros; importar XLSX |
| `/app/fornecedores/{id}` | Detalhe do fornecedor | Dados completos; produtos mapeados |
| `/app/vendas` | Vendas | PDV balcão; tabela de vendas; "Nova Venda"; "Nova OS" |
| `/app/vendas/nova` | Nova Venda | Itens com busca de produto; cliente opcional; total calculado |
| `/app/usuarios` | Usuários | CRUD completo; ADMIN only |

---

## 9. Entrada de NF-e — Requisito Detalhado

### Objetivo

Permitir que o operador importe uma Nota Fiscal Eletrônica de compra (NF-e v4.00) enviando o arquivo XML. O sistema deve:

1. Identificar e upsert o fornecedor emitente pelo CNPJ.
2. Criar um **rascunho de entrada** com os itens da NF-e.
3. Tentar vincular automaticamente cada item ao produto cadastrado no estoque.
4. Permitir que o operador revise, corrija e confirme a entrada — atualizando o estoque apenas na confirmação.

### Matching Automático de Produtos

Ao criar o rascunho, cada item passa por **4 tentativas de vínculo em ordem de prioridade**:

| Prioridade | Estratégia | Campo NF-e | Campo Estoque |
|---|---|---|---|
| 1 | Mapeamento aprendido | `cProd` + `fornecedor_id` | `mapeamento_fornecedor_produto` |
| 2 | Cód. Estoque via código de referência | Prefixo numérico de `xProd` (`codigo_ref`) | `produto.codigo` |
| 3 | Cód. Estoque via código do fornecedor | `cProd` diretamente | `produto.codigo` |
| 4 | EAN/GTIN | `cEAN` (se válido, ≥ 8 dígitos) | `produto.ean` |

**Mapeamento aprendido:** na confirmação, registra `(fornecedor_id, cProd) → produto_id`. Na reimportação, itens chegam `AUTO_VINCULADO` automaticamente.

**`codigo_ref`:** primeiro token de `xProd` se contiver ao menos um dígito e tiver entre 2 e 25 caracteres.
- `"32208 AMORTECEDOR DIANT"` → `codigo_ref = "32208"` ✓
- `"KIT AMORT TRAS E/D"` → `codigo_ref = None` (sem dígito no primeiro token)

**Status dos itens:**

| Status | Significado |
|---|---|
| `AUTO_VINCULADO` | Vinculado automaticamente (qualquer das 4 estratégias) |
| `VINCULADO` | Vinculado manualmente pelo operador |
| `NOVO` | Operador criou novo produto a partir dos dados da NF-e |
| `PENDENTE` | Sem vínculo — bloqueia o Confirmar |

### Criação de Produto a partir da NF-e

| Campo do Produto | Origem |
|---|---|
| `codigo` | `codigo_ref` (se extraído) ou `cProd` |
| `descricao` | `xProd` |
| `ncm` | `NCM` |
| `ean` | `cEAN` (se válido) |
| `preco_custo` | `vUnCom` |
| `preco_venda` | `vUnCom` (ajustar manualmente depois) |
| `estoque_atual` | `0` (atualizado na confirmação) |

### Ciclo de Vida da Entrada NF-e

```
RascunhoEntrada (PENDENTE)
        │  POST /rascunhos/{id}/confirmar
        │  (todos os itens vinculados)
        ▼
EntradaNfe (ABERTA)  ← atendente edita data_entrada
        │  PATCH /entradas/{id}
        ▼
EntradaNfe (PROCESSADA)
```

### Regras de Negócio

| Regra | Comportamento |
|---|---|
| NF-e já importada | `NFeJaImportada` 409 — identificada pela chave de 44 dígitos |
| Rascunho confirmado/cancelado | `RascunhoJaConfirmado` 409 |
| Confirmar com pendentes | `RascunhoPendente` 422 |
| EAN inválido (`SEM GTIN`, `"0"`, < 8 dígitos) | Ignorado; item fica sem EAN |
| Entrada já processada | `EntradaJaProcessada` 409 — somente leitura |

### NF-e de Referência para Testes

Arquivo: `src/oficinas/modules/estoque/tests/fixtures/nfxml/31260545987005028360550010003538181116087337.xml`

| Campo | Valor |
|---|---|
| Chave | `31260545987005028360550010003538181116087337` |
| Emitente | COMERCIAL AUTOMOTIVA S.A. |
| CNPJ emitente | `45987005028360` |
| Número NF | `353818` / Série `1` |
| Data emissão | `2026-05-21` |
| Valor total | R$ 586,20 |

| # | cProd | Descrição | Qtd | Preço unit. | EAN | codigo_ref |
|---|---|---|---|---|---|---|
| 1 | `93031` | KIT AMORT TRAS E/D 1 BT/CF/CX | 2 | R$ 115,44 | `7891579313171` | `None` |
| 2 | `3327591` | AMORTECEDOR TRASEIRO ESQ/DIR | 2 | R$ 177,66 | `7899027348942` | `None` |

---

## 10. Segurança

### Autenticação e Autorização
- JWT Bearer com expiração configurável (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- RLS PostgreSQL garante isolamento de tenant sem lógica no código
- `SET LOCAL app.current_tenant = :tid` aplicado em toda sessão tenant-scoped
- Dependências: `requer_autenticado`, `requer_atendente_acima`, `requer_admin`

### Validação de Inputs
- Busca ILIKE: wildcards `%` e `_` do usuário são escapados antes de montar o padrão (`replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")`)
- Sem SQL injection: todo acesso ao banco usa SQLAlchemy ORM com binding parametrizado ou `text()` com `:param` nomeados

---

## 11. Migrations SQL

| Arquivo | O que cria/altera |
|---|---|
| `001_global_schema.sql` | Schema `global`, tabelas `veiculo` e `historico_veiculo` (append-only) |
| `002_tenant_schema.sql` | Schema `public`: tenant, usuario, cliente, cliente_veiculo, fornecedor, produto, entrada_nfe, item_entrada, movimentacao_estoque, ordem_servico, item_os, venda, item_venda, nota_fiscal_saida, agente_sessao |
| `003_rls_policies.sql` | RLS FORCE em todas as tabelas tenant-scoped + policies `tenant_iso` |
| `004_seed.sql` | Tenant demo + usuário admin demo |
| `005_iam_adjustments.sql` | `mecanico_id` DROP NOT NULL; `aberto_por_id` em OS; `email` DROP NOT NULL em usuario |
| `006_nfe_rascunho.sql` | `produto.ean`; `mapeamento_fornecedor_produto`; `rascunho_entrada`; `item_rascunho_entrada` |
| `007_entrada_data_entrada.sql` | `entrada_nfe.data_entrada`; `item_entrada.data_entrada` |
| `008_fornecedor_expanded.sql` | `fornecedor`: nome_fantasia, ie, telefone, email; `item_rascunho_entrada`: cfop, cst |
| `009_apontamento_os.sql` | `apontamento_os` com índice em os_id |
| `010_fornecedor_ativo_tipo.sql` | `fornecedor.ativo`; `fornecedor.tipo_pessoa` |
| `011_produto_campos_extras.sql` | `produto`: unidade_medida, ref_fabricante, peso_liquido/bruto, origem_mercadoria, observacoes |
| `012_cliente_campos_extras.sql` | `cliente`: tipo_pessoa, celular, rg, data_nascimento, sexo, apelido, cep, cidade, uf, observacoes, consumidor_final, indicador_ie, inscricao_estadual, ativo |

---

## 12. Enums (fonte única — `core/enums.py`)

```
Perfil:            ADMIN · ATENDENTE · MECANICO
StatusOS:          ABERTA · EM_EXECUCAO · AGUARDANDO_PECA · FECHADA · CANCELADA
TipoMovimentacao:  ENTRADA · SAIDA · RESERVA · LIBERACAO
TipoItem:          PECA · SERVICO
OrigemVenda:       BALCAO · OS
TipoVeiculo:       carro · moto · caminhao · van
StatusRascunho:    PENDENTE · CONFIRMADA · CANCELADA
StatusItem:        AUTO_VINCULADO · VINCULADO · NOVO · PENDENTE
StatusEntradaNfe:  ABERTA · PROCESSADA
RegimeTributario:  simples · lucro_presumido · lucro_real
```

---

## 13. O Que Não Existe Ainda (YAGNI)

- Agente WhatsApp (mecânico abre OS por mensagem via Claude)
- Emissão de NF-e / NFCe (módulo fiscal + certificado A1)
- Relatórios e dashboards gerenciais
- Multi-filial / multi-tenant management
- App nativo iOS/Android
- Marketplace de peças
- Módulo financeiro (contas a pagar/receber, DRE)
- Agendamento de serviços
- Notificação automática de retorno ao cliente
- Integração com maquininha de pagamento
- Cotação online de peças
- Infra Docker Compose + CI/CD (apenas desenvolvimento local por ora)
