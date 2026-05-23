# Requisitos — Importação de NF-e por XML

> Módulo: `apps/oficinas` · Domínio: `estoque`

---

## 1. Objetivo

Permitir que o operador importe uma Nota Fiscal Eletrônica de compra (NF-e v4.00) enviando o arquivo XML. O sistema deve:

1. Identificar e upsert o fornecedor emitente pelo CNPJ.
2. Criar um **rascunho de entrada** com os itens da NF-e.
3. Tentar vincular automaticamente cada item ao produto cadastrado no estoque.
4. Permitir que o operador revise, corrija e confirme a entrada — atualizando o estoque apenas na confirmação.

---

## 2. Fluxo Completo (Frontend)

```
Wizard — 3 passos de importação

  Passo 1 — Importação
    Upload do arquivo .xml
    → POST /entradas/xml
    → Retorna RascunhoResponse

  Passo 2 — Fornecedor
    Exibe dados do emitente já upsertados na base
    Campos editáveis: Razão Social, Nome Fantasia, CNPJ, Inscrição Estadual,
                      Telefone, E-mail
    → PATCH /fornecedores/{id}  (opcional, antes de avançar)

  Passo 3 — Produtos
    Tabela com todos os itens da NF-e e seus status
    Colunas: Cód. Estoque, Marca, Cód. Fornecedor, Descrição, Qtd, R$ Compra,
             Margem %, R$ Venda, NCM, CST, CFOP, EAN, Status

    Itens AUTO_VINCULADO/VINCULADO/NOVO:
      Cód. Estoque exibe o produto.codigo vinculado (somente leitura)
      Marca exibe produto.marca (somente leitura)

    Itens PENDENTE:
      Cód. Estoque fica editável — operador digita o código do produto na base
      Busca em tempo real por produto.codigo enquanto digita
      Ao selecionar produto → vincula automaticamente via PATCH
      Alternativa: botão "Criar novo" cria produto com dados da NF-e

    → PATCH /entradas/rascunhos/{id}/itens/{item_id}
    Botão "Concluir" habilitado apenas quando pendentes = 0
    → POST /entradas/rascunhos/{id}/confirmar
    → Redireciona para /estoque/entrada/{entrada_id}

Tela de Edição da Entrada (pós-wizard)

  Exibe Dados da Nota: número, chave, data de emissão, valor total
  Campo editável: Data de Entrada (da nota inteira)
  Tabela de itens com campo Dt. Entrada editável por item
  Botão "Salvar" → PATCH /entradas/{entrada_id}
    → Grava as datas e transiciona para status PROCESSADA (financeiro)
```

---

## 3. Fornecedor — Upsert por CNPJ

- O CNPJ do `<emit>` identifica o fornecedor.
- Se já existir na base (mesmo CNPJ e tenant): retorna o registro existente sem alterar.
- Se não existir: cria novo com `razao_social` e `cnpj` do XML.
- O operador pode editar os dados no Passo 2 via `PATCH /fornecedores/{id}`.
- O `fornecedor_id` é vinculado ao rascunho para uso no mapeamento automático.

---

## 4. Matching Automático de Produtos

Ao criar o rascunho, cada item da NF-e passa por **4 tentativas de vínculo em ordem de prioridade**. O `produto.codigo` (Código de Estoque) é o identificador primário de vinculação na base.

| Prioridade | Estratégia | Campo NF-e | Campo Estoque |
|---|---|---|---|
| 1 | Mapeamento aprendido | `cProd` + `fornecedor_id` | `mapeamento_fornecedor_produto` |
| 2 | Cód. Estoque via código de referência | Prefixo numérico de `xProd` (`codigo_ref`) | `produto.codigo` |
| 3 | Cód. Estoque via código do fornecedor | `cProd` diretamente | `produto.codigo` |
| 4 | EAN/GTIN | `cEAN` (se válido, ≥ 8 dígitos) | `produto.ean` |

**Prioridade 1 — Mapeamento aprendido:** na confirmação, o sistema registra `(fornecedor_id, cProd) → produto_id`. Na reimportação do mesmo fornecedor, o item já chega `AUTO_VINCULADO` sem precisar das demais estratégias.

**Prioridade 2 — `codigo_ref`:** o primeiro token da descrição (`xProd`) é extraído se contiver ao menos um dígito e tiver entre 2 e 25 caracteres, e comparado com `produto.codigo`.
- `"32208 AMORTECEDOR DIANT"` → `codigo_ref = "32208"` → busca `produto.codigo = "32208"` ✓
- `"KIT AMORT TRAS E/D"` → `codigo_ref = None` (sem dígito no primeiro token)

**Prioridade 3 — `cProd` direto:** alguns fornecedores usam como `cProd` o próprio código de estoque do comprador. Se nenhuma estratégia anterior funcionou, tenta `produto.codigo == cProd`.

**Prioridade 4 — EAN:** fallback para itens sem código de estoque identificável.

**Status dos itens após o matching:**

| Status | Significado |
|---|---|
| `AUTO_VINCULADO` | Vinculado automaticamente pelo sistema (qualquer das 4 estratégias) |
| `VINCULADO` | Vinculado manualmente pelo operador via Cód. Estoque |
| `NOVO` | Operador criou novo produto a partir dos dados da NF-e |
| `PENDENTE` | Sem vínculo — bloqueia o Concluir |

---

## 5. Resolução Manual por Código de Estoque

Itens que ficaram `PENDENTE` após o auto-matching são resolvidos pelo operador no Passo 3.

**Fluxo de resolução via Cód. Estoque:**

1. A célula "Cód. Estoque" do item fica como campo de texto editável.
2. Enquanto o operador digita, o frontend busca em tempo real por `produto.codigo` (busca por prefixo ou igual — `GET /produtos?q=<codigo>`).
3. O operador seleciona o produto na lista → o sistema chama `PATCH /rascunhos/{id}/itens/{item_id}` com `{acao: "vincular", produto_id}`.
4. O item passa para status `VINCULADO` e o campo exibe o `produto.codigo` como somente leitura.

**Alternativa — Criar novo produto:**

Se nenhum produto corresponder, o operador pode acionar "Criar novo". O sistema cria um `Produto` usando os dados do item da NF-e (ver Seção 6) e vincula ao item com status `NOVO`.

**Bloqueio:** o botão "Concluir" permanece desabilitado enquanto `pendentes > 0`.

---

## 6. Mapeamento Aprendido

Após cada confirmação bem-sucedida, o sistema registra `mapeamento_fornecedor_produto`:

```
fornecedor_id + codigo_fornecedor (cProd)  →  produto_id
```

Este registro garante que na **próxima importação do mesmo fornecedor**, qualquer item com o mesmo `cProd` seja vinculado automaticamente via Prioridade 1 — independentemente de EAN, código de referência ou código de estoque.

**Importante:** o mapeamento aprende independentemente de como o vínculo foi estabelecido (auto ou manual). Após o operador resolver um item PENDENTE via Cód. Estoque e confirmar a entrada, a associação `cProd → produto` desse fornecedor fica registrada para sempre.

---

## 7. Criação de Produto a partir da NF-e

Quando o operador escolhe `acao = "criar_novo"`:

| Campo do Produto | Origem |
|---|---|
| `codigo` | `codigo_ref` (se extraído) ou `codigo_fornecedor` (`cProd`) |
| `descricao` | `xProd` |
| `ncm` | `NCM` |
| `ean` | `cEAN` (se válido) |
| `preco_custo` | `vUnCom` |
| `preco_venda` | `vUnCom` (operador deve ajustar depois) |
| `estoque_atual` | `0` (atualizado na confirmação) |

---

## 8. Confirmação — Impacto no Estoque

A confirmação (`POST /confirmar`) só é permitida quando todos os itens estiverem vinculados (`pendentes = 0`).

Ao confirmar:
1. Cria `EntradaNfe` com `status = ABERTA`.
2. Cria `ItemEntrada` para cada item.
3. Registra `MovimentacaoEstoque` com `tipo_mov = ENTRADA` para cada item — incrementa `produto.estoque_atual`.
4. Aprende/atualiza `mapeamento_fornecedor_produto` para cada item com fornecedor definido.
5. Atualiza `rascunho.status = CONFIRMADA`.
6. Redireciona o operador para a tela de edição da entrada (`/estoque/entrada/{id}`).

---

## 9. Ciclo de Vida da Entrada NF-e

```
RascunhoEntrada (PENDENTE)
        │
        │  POST /rascunhos/{id}/confirmar
        │  (todos os itens vinculados)
        ▼
EntradaNfe (ABERTA)
        │   ← atendente edita data_entrada da nota e dos itens
        │
        │  PATCH /entradas/{id}
        │  (salvar datas → envia ao financeiro)
        ▼
EntradaNfe (PROCESSADA)
```

**Status `ABERTA`:** entrada criada, estoque já atualizado. O atendente pode corrigir a data de entrada da nota e de cada item antes de finalizar.

**Status `PROCESSADA`:** entrada fechada e enviada ao financeiro. Nenhuma edição adicional é permitida.

---

## 10. Regras de Negócio

| Regra | Comportamento |
|---|---|
| NF-e já importada | `NFeJaImportada` (409) — identificada pela `chave_nfe` de 44 dígitos |
| Rascunho confirmado ou cancelado | Nenhuma edição permitida — `RascunhoJaConfirmado` (409) |
| Confirmar com pendentes | `RascunhoPendente` (422) — informa quantos itens faltam |
| EAN inválido (`SEM GTIN`, `"0"`, menos de 8 dígitos) | Ignorado; item fica sem EAN |
| Cancelar rascunho | `DELETE /rascunhos/{id}` — sem impacto no estoque |
| Editar entrada já processada | `EntradaJaProcessada` (409) — entrada em status PROCESSADA é somente leitura |
| `data_entrada` padrão | Não preenchida na confirmação; atendente define na tela de edição |

---

## 11. Endpoints da API

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| `POST` | `/entradas/xml` | ADMIN | Upload do XML → cria rascunho |
| `GET` | `/entradas/rascunhos` | ATENDENTE+ | Listar rascunhos |
| `GET` | `/entradas/rascunhos/{id}` | ATENDENTE+ | Detalhar rascunho + itens |
| `PATCH` | `/entradas/rascunhos/{id}/itens/{item_id}` | ADMIN | Vincular item |
| `POST` | `/entradas/rascunhos/{id}/confirmar` | ADMIN | Confirmar → cria EntradaNfe (ABERTA) |
| `DELETE` | `/entradas/rascunhos/{id}` | ADMIN | Cancelar rascunho |
| `GET` | `/entradas/{id}` | ATENDENTE+ | Detalhar entrada + itens |
| `PATCH` | `/entradas/{id}` | ADMIN | Salvar datas e processar para financeiro (ABERTA → PROCESSADA) |
| `GET` | `/fornecedores/{id}` | ATENDENTE+ | Detalhar fornecedor |
| `PATCH` | `/fornecedores/{id}` | ADMIN | Atualizar dados do fornecedor |

---

## 12. NF-e de Referência para Testes

Arquivo: `src/oficinas/modules/estoque/tests/fixtures/nfxml/31260545987005028360550010003538181116087337.xml`

| Campo | Valor |
|---|---|
| Chave | `31260545987005028360550010003538181116087337` |
| Emitente | COMERCIAL AUTOMOTIVA S.A. |
| CNPJ emitente | `45987005028360` |
| Número NF | `353818` / Série `1` |
| Data emissão | `2026-05-21` |
| Valor total | R$ 586,20 |

**Itens:**

| # | cProd | Descrição | Qtd | Preço unit. | EAN | código_ref |
|---|---|---|---|---|---|---|
| 1 | `93031` | KIT AMORT TRAS E/D 1 BT/CF/CX | 2 | R$ 115,44 | `7891579313171` | `None` |
| 2 | `3327591` | AMORTECEDOR TRASEIRO ESQ/DIR | 2 | R$ 177,66 | `7899027348942` | `None` |

Ambos os itens só são vinculados automaticamente via **EAN** ou **mapeamento aprendido** — a estratégia de código de referência não se aplica pois as descrições começam com palavras sem dígito.
