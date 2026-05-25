# LGPD — Estratégia de Conformidade

> Documento vivo. Atualizar sempre que um novo dado pessoal for coletado ou uma base legal mudar.
> Data da última revisão: 2026-05-25

---

## 1. Inventário de Dados Pessoais

### apps/producao (rastreabilidade agro)

| Entidade | Campos PII | Classificação |
|---|---|---|
| `Account` | nome, documento (CPF/CNPJ), email, whatsapp_phone | Dados pessoais comuns |
| `User` | nome, email, senha_hash | Dados pessoais comuns |
| `WhatsappSessao` | phone (E.164), profile_name | Dados pessoais comuns |
| `WhatsappMensagem` | corpo (conteúdo livre), midia_urls | Dados pessoais — conteúdo indeterminado |
| `message_queue` (PostgreSQL) | phone, messages (JSONB raw) | Dados pessoais — transiente, mas persistido |

### apps/oficinas (gestão de oficinas)

| Entidade | Campos PII | Classificação |
|---|---|---|
| `Cliente` | nome, cpf_cnpj, **rg**, **data_nascimento**, **sexo**, telefone, celular, email, endereço completo | **Dados sensíveis** (sexo + dados que permitem inferência) |
| `Usuario` | nome, email, numero_whatsapp, senha_hash | Dados pessoais comuns |
| `Tenant` | razao_social, cnpj | Dados de PJ (fora do escopo LGPD) |
| `Fornecedor` | cnpj, telefone, email (pode ser de pessoa física) | Dados pessoais se PF |
| `global.veiculo` | placa, chassi | Quasi-pessoal (vinculado ao dono via `cliente_veiculo`) |
| `agente_sessao` | numero_whatsapp, mensagens JSONB (histórico Claude) | Dados pessoais — alta sensibilidade |
| `historico_veiculo` | resumo_publico, detalhe_privado | Pode conter dados pessoais nos textos livres |

---

## 2. Análise de Risco

### Risco Alto

- **`Cliente.sexo` e `Cliente.data_nascimento`** — dados sensíveis (Art. 5, II LGPD). Exigem base legal específica e consentimento explícito ou obrigação legal. NFCe não exige esses campos; revisar necessidade.
- **`agente_sessao.mensagens`** — histórico completo de conversas com Claude armazenado em JSONB sem TTL definido. O mecânico pode mencionar dados de terceiros (clientes, placas, informações médicas).
- **`message_queue` no producao** — mensagens WhatsApp brutas em PostgreSQL sem política de retenção explícita.

### Risco Médio

- **`WhatsappMensagem.corpo`** — conteúdo livre; o titular pode enviar dados pessoais de terceiros.
- **`historico_veiculo.detalhe_privado`** — campo texto livre, append-only, nunca deletável por design. Conflito potencial com o direito de eliminação (Art. 18, VI). Mitigação: anonimizar referências ao titular no texto, não deletar o registro do veículo.
- **Ausência de endpoints** para exercício de direitos dos titulares (acesso, correção, portabilidade, eliminação).

### Risco Baixo / Estrutural

- Senhas em hash — verificar algoritmo (bcrypt com fator ≥ 12 ou argon2id).
- RLS no PostgreSQL já isola dados por tenant.
- Logs estruturados com IDs, sem PII exposta (confirmar em todos os serviços).

---

## 3. Base Legal por Operação de Tratamento (Art. 7 e 11)

| Dado | Base Legal Adequada | Artigo |
|---|---|---|
| Account/User — email, nome | Execução de contrato | Art. 7, V |
| Cliente — CPF/CNPJ | Obrigação legal + execução de contrato | Art. 7, II e V |
| Cliente — sexo, data_nascimento | **Consentimento explícito** — avaliar se é necessário | Art. 7, I + Art. 11, I |
| Mecânico — numero_whatsapp | Execução de contrato (vínculo empregatício) | Art. 7, V |
| WhatsApp — mensagens | Interesse legítimo + consentimento informado na primeira interação | Art. 7, IX |
| Histórico de veículo | Execução de contrato + interesse legítimo | Art. 7, V e IX |
| Fornecedor PF — email, telefone | Execução de contrato | Art. 7, V |

---

## 4. Direitos dos Titulares (Art. 18)

Atualmente **ausentes** no código. Implementar:

```
# apps/producao
GET    /privacy/me                  → dados do usuário autenticado (acesso)
PUT    /privacy/me                  → correção de dados
DELETE /privacy/me/account          → encerramento (anonimização + soft delete)

# apps/oficinas
GET    /privacy/cliente/{id}        → relatório de dados (portabilidade — export JSON)
PUT    /privacy/cliente/{id}        → correção (já existe via CRUD; validar cobertura)
DELETE /privacy/cliente/{id}/anonimizar → anonimiza PII, preserva vínculos fiscais
```

**Estratégia de anonimização de cliente:**
Substituir `nome`, `cpf_cnpj`, `rg`, `telefone`, `celular`, `email` por tokens opacos (ex: `ANONIMIZADO-{uuid}`). Manter `tenant_id` e vínculos de `cliente_veiculo` e `ordem_servico` para integridade fiscal. Não deletar o registro.

---

## 5. Política de Retenção e Descarte

| Dado | Retenção Atual | Política Proposta | Implementação |
|---|---|---|---|
| `message_queue` (producao) | Sem TTL | 30 dias | Job diário: `DELETE WHERE created_at < now() - interval '30 days' AND status = 'processed'` |
| `WhatsappMensagem` | Indefinida | 90 dias, depois anonimizar corpo | Job semanal |
| `agente_sessao.mensagens` | 2h de timeout de sessão, mas persiste | Purgar mensagens ao expirar sessão; manter só metadados | No worker, após timeout |
| `historico_veiculo` | Permanente (append-only — intencional) | Não deletar; separar dados do titular dos dados do veículo no texto | Disciplina de escrita no agente |
| NF-e XML (`xml_path`) | Permanente (obrigação fiscal) | Mínimo 5 anos — obrigação legal | Não alterar |

---

## 6. Subprocessadores

O projeto transmite dados pessoais para serviços externos. É necessário verificar DPA (Data Processing Agreement) e adequação transfronteiriça (Art. 33).

| Subprocessador | Dados Enviados | Verificação Necessária |
|---|---|---|
| **Twilio** | phone (E.164), profile_name, corpo das mensagens | DPA + confirmar localização dos dados (Brasil ou países adequados) |
| **Anthropic (Claude API)** | Mensagens do agente contendo dados de clientes da oficina | Verificar termos de uso de dados da API; solicitar DPA se disponível |

**Ação:** adicionar cláusula no Aviso de Privacidade informando uso de subprocessadores e as finalidades.

---

## 7. Segurança Técnica (Art. 46)

- [ ] Confirmar algoritmo de hash de senha: `bcrypt` (fator ≥ 12) ou `argon2id`
- [ ] Garantir que logs estruturados nunca imprimem CPF, phone, corpo de mensagem — apenas IDs
- [ ] Avaliar criptografia em repouso para `cpf_cnpj` e `rg` via `pgcrypto` (custo/benefício para MVP)
- [ ] Política de senha mínima no `UserCreate` (comprimento, complexidade)
- [ ] Revisar CORS — `FRONTEND_URL` restrito em produção (já previsto no config)
- [ ] Verificar se `TWILIO_VALIDATE_SIGNATURE=True` está ativo em produção

---

## 8. Registro de Operações de Tratamento — RoPA (Art. 37)

A ser elaborado antes do lançamento em produção. Modelo mínimo por operação:

| Campo | Descrição |
|---|---|
| Nome da operação | Ex: "Cadastro de cliente para emissão de OS" |
| Controlador | Nome da empresa operadora do tenant |
| Finalidade | Finalidade específica e legítima |
| Base legal | Art. 7 ou 11 aplicável |
| Categorias de titulares | Ex: clientes PF da oficina |
| Categorias de dados | Ex: nome, CPF, telefone, endereço |
| Prazo de retenção | Ex: 5 anos por obrigação fiscal |
| Subprocessadores | Ex: Twilio, Anthropic |
| Medidas de segurança | Ex: RLS, hash de senha, HTTPS |

---

## 9. Priorização

### Sprint imediato — bloqueadores legais

- [ ] Avaliar necessidade de `sexo` e `data_nascimento` no MVP → remover se não houver base legal clara
- [ ] Adicionar TTL e job de limpeza em `message_queue` (producao)
- [ ] Verificar e assinar DPA com Twilio e Anthropic
- [ ] Incluir consentimento informado na primeira mensagem WhatsApp do agente

### Próximo sprint — compliance básico

- [ ] Endpoint `GET /privacy/me` (producao) — acesso aos dados pelo titular
- [ ] Endpoint `DELETE /privacy/cliente/{id}/anonimizar` (oficinas)
- [ ] Purge de `agente_sessao.mensagens` após expirar sessão
- [ ] Aviso de Privacidade redigido e publicado

### Médio prazo — maturidade

- [ ] RoPA completo por operação de tratamento (Art. 37)
- [ ] Endpoint de portabilidade — export JSON dos dados do titular
- [ ] Criptografia de colunas sensíveis (`cpf_cnpj`, `rg`) via `pgcrypto`
- [ ] Nomeação de Encarregado de Dados (DPO) — obrigatório se volume de dados crescer (Art. 41)
- [ ] Plano de resposta a incidentes (Art. 48 — notificação à ANPD em 72h)
