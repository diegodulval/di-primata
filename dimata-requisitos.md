# Di Mata × Primata — Modelagem de Requisitos, Entidades e Relacionamentos

> **Versão:** 2.0 · **Referência normativa:** PGA-RASTREABILIDADE / SISBOV · IN MAPA nº 51/2018 · IN nº 17/2006 · Decreto nº 7.623/2011  
> Plataforma universal de rastreabilidade de cadeia produtiva — agnóstica de setor.

-----

## Sumário

1. [Contexto e Propósito](#1-contexto-e-propósito)
1. [Requisitos Funcionais](#2-requisitos-funcionais)
1. [Requisitos Não Funcionais](#3-requisitos-não-funcionais)
1. [Regras de Negócio](#4-regras-de-negócio)
1. [Entidades de Negócio](#5-entidades-de-negócio)
1. [Enumerações e Tipos](#6-enumerações-e-tipos)
1. [Modelo de Relacionamento (ERD Textual)](#7-modelo-de-relacionamento-erd-textual)
1. [Diagrama UML de Classes](#8-diagrama-uml-de-classes)
1. [Fluxo Principal do Sistema](#9-fluxo-principal-do-sistema)
1. [Perfis de Acesso](#10-perfis-de-acesso)
1. [Módulos do Sistema](#11-módulos-do-sistema)

-----

## 1. Contexto e Propósito

O **Di Mata** é uma plataforma de rastreabilidade de cadeia produtiva agnóstica de setor — conecta a origem de qualquer produto ao consumidor final, passando por todos os processos intermediários.

O **Primata** é o agente de IA embarcado que captura, transcreve e estrutura os registros em campo ou no chão de fábrica, alimentando o Di Mata em tempo real.

### 1.1 Setores Suportados

|Setor                |Exemplos de Unidade            |Exemplos de Ciclo              |
|---------------------|-------------------------------|-------------------------------|
|Agropecuária         |Talhão, pasto, canteiro        |Safra, colheita, temporada     |
|Indústria            |Linha de produção, célula, tear|Ordem de Produção (OP), remessa|
|Artesanato / Cultural|Ateliê, oficina, baia          |Encomenda, série, tiragem      |
|Florestal / Ambiental|Área de manejo, viveiro        |Ciclo de extração, remessa     |

### 1.2 Definição de Rastreabilidade (base normativa)

> *“Rastreabilidade é o conjunto de ações, medidas e procedimentos adotados para caracterizar a **origem, o estado sanitário/de conformidade, a produção e a produtividade** de uma cadeia produtiva e a segurança dos produtos provenientes dessa exploração econômica.”*  
> — Adaptado da IN MAPA nº 51/2018, generalizado para todas as cadeias produtivas.

-----

## 2. Requisitos Funcionais

### RF-01 — Cadastro do Agente Produtor

- O sistema deve permitir o cadastro de pessoas físicas ou jurídicas de qualquer setor produtivo.
- Atributos obrigatórios: nome, documento (CPF/CNPJ), email, tipo de agente, plano de assinatura, setor primário.
- Um agente pode ter múltiplas unidades produtivas em setores distintos.

### RF-02 — Cadastro de Unidade Produtiva

- O sistema deve permitir o cadastro de unidades produtivas vinculadas a um agente.
- A unidade define o template de setor que governa os tipos de processo disponíveis.
- Atributos: nome, tipo (`TALHAO`, `LINHA`, `TEAR`, `ATELIE`, `BAIA`), área/capacidade, coordenadas geográficas (lat/lng), setor template.

### RF-03 — Protocolo de Processo

- O sistema deve suportar templates configuráveis de processo por setor.
- Cada protocolo define um conjunto de etapas, quais são obrigatórias e a referência normativa aplicável.
- O sistema **não deve permitir** a geração de lote se etapas obrigatórias não foram registradas.

### RF-04 — Ciclo Produtivo

- O sistema deve permitir a abertura de ciclos produtivos (safra / OP / encomenda) por unidade.
- Um ciclo deve ter: produto, data de início, insumos de entrada e protocolo associado.
- O ciclo segue a máquina de estados: `ABERTO → EM_PRODUCAO → ENCERRADO → VALIDANDO → LOTE_GERADO → ARQUIVADO`.

### RF-05 — Registro de Processos e Insumos

- O sistema deve registrar qualquer evento do ciclo: entrada de insumo, operação, controle de qualidade, anomalia, movimentação.
- Registros são **imutáveis** após validação. Correções criam um novo registro de aditamento vinculado ao original.
- O timestamp do registro é o do dispositivo no momento da captura, não da sincronização.
- Campos obrigatórios: tipo de evento, descrição, payload estruturado (JSONB), origem da captura, timestamp de captura.

### RF-06 — Geração de Lote Rastreável

- O sistema deve consolidar automaticamente os registros validados de um ciclo encerrado em um lote com código único e QR Code.
- O código do lote segue o formato: `[SETOR]-[UNIDADE]-[ANO]-[SEQ]` (ex: `CAF-VGH-2026-0042`).
- O código e o snapshot do lote são **imutáveis** após geração.
- A geração só ocorre se todas as etapas obrigatórias do protocolo estiverem cumpridas.

### RF-07 — Portal Público do Consumidor

- O sistema deve disponibilizar uma interface pública acessada via QR Code, sem necessidade de login.
- O portal exibe: origem do insumo, processos, operadores, datas, certificações e história do produtor.
- O portal **não deve exibir** dados financeiros, custos ou margens.

### RF-08 — Painel do Certificador / Consultor

- O sistema deve oferecer uma visão analítica do ciclo para o agente validador.
- O certificador pode aprovar ou sinalizar não conformidade em registros individuais.
- O certificador assina digitalmente o lote antes da geração do QR.
- O vínculo do certificador é com a **unidade produtiva**, não com o agente produtor.

### RF-09 — Cadeia Integrada (Farm-to-Fork)

- O sistema deve suportar o vínculo entre um lote de produto final e múltiplos lotes de insumo (relação N:N).
- O sistema deve suportar recall reverso: dado um lote de insumo defeituoso, identificar todos os lotes de produto afetados.
- Um fornecedor externo pode ter seus lotes de insumo vinculados com nota fiscal e certificado.

### RF-10 — Agente Primata (Captura em Campo)

- O Primata deve capturar registros por voz, foto ou leitura de QR/código de barras.
- Toda captura deve ser apresentada ao operador para confirmação antes de gravar.
- O Primata deve operar em modo offline, armazenando eventos em fila local e sincronizando por ordem cronológica quando reconectar.
- O Primata deve alertar quando uma etapa obrigatória do protocolo estiver atrasada ou faltante.

### RF-11 — Controle de Qualidade Inline (Industrial)

- O sistema deve suportar o registro de inspeções durante o processo com critério de aprovação por etapa.
- Uma não conformidade em ponto crítico deve bloquear a geração do lote.

### RF-12 — Rastreabilidade de Fornecedor (Industrial Premium)

- O sistema deve suportar a vinculação de certificados do fornecedor (NF, laudo de qualidade, cert. de material) ao lote de insumo.

### RF-13 — Gestão de Máquinas e Manutenção (Industrial Premium)

- O sistema deve registrar setup, calibrações e manutenções preventivas por equipamento.
- O registro de manutenção deve ser vinculável ao lote produzido no período.

### RF-14 — Módulo de Custos (Premium Agro)

- O sistema deve permitir o registro de custos de insumos, mão de obra e despesas por ciclo e por unidade.
- Dados financeiros são visíveis **somente** ao agente produtor com plano Premium.

### RF-15 — Auditoria de Ações

- O sistema deve registrar em log imutável toda ação de criação, atualização de status e geração de lote.
- O log deve conter: entidade afetada, ator, ação, dados antes/depois, timestamp.

-----

## 3. Requisitos Não Funcionais

|ID    |Requisito                  |Detalhe                                                                  |
|------|---------------------------|-------------------------------------------------------------------------|
|RNF-01|Agnóstico de banco de dados|Modelo lógico puro — sem dependência de engine específica                |
|RNF-02|Imutabilidade de registros |Registros validados e lotes gerados nunca são alterados — apenas aditados|
|RNF-03|Offline-first (Primata)    |Captura funciona sem rede; sync ordenada por `capturado_em`              |
|RNF-04|Multi-setor                |Um agente pode operar múltiplos setores em uma única conta               |
|RNF-05|Multi-tenant               |Isolamento total de dados por `agente_id`                                |
|RNF-06|Rastreabilidade completa   |Toda ação é logada; nenhum dado é deletado                               |
|RNF-07|QR público sem autenticação|O portal do consumidor não exige conta ou login                          |
|RNF-08|Conformidade normativa     |Compatível com os princípios da IN MAPA nº 51/2018 e ISO 22005           |
|RNF-09|Extensibilidade via JSONB  |Payloads flexíveis sem quebrar o schema ao adicionar novos tipos         |
|RNF-10|Idempotência no sync       |`device_id + capturado_em` como chave natural anti-duplicata             |

-----

## 4. Regras de Negócio

### 4.1 Integridade e Rastreabilidade do Lote

|ID   |Regra                                                                                                                                    |
|-----|-----------------------------------------------------------------------------------------------------------------------------------------|
|RN-01|**Lote só é gerado com protocolo 100% completo.** Todas as etapas obrigatórias devem ter ao menos um registro válido.                    |
|RN-02|**Código do lote é único, sequencial e imutável.** Formato: `[SETOR]-[UNIDADE]-[ANO]-[SEQ]`. Nunca reutilizado.                          |
|RN-03|**Registros são imutáveis após validação.** Correções geram novo registro de aditamento vinculado ao original.                           |
|RN-04|**Registro inválido fica visível ao produtor, oculto no QR público.** O evento existe na base mas não aparece na rastreabilidade pública.|

### 4.2 Cadeia Integrada e Fornecedores

|ID   |Regra                                                                                                                                                                   |
|-----|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|RN-05|**Insumo de fornecedor externo pode ser vinculado ao lote com certificado.** O produto final herda a rastreabilidade do insumo quando o fornecedor também usa o Di Mata.|
|RN-06|**Um lote de produto final pode ter múltiplos lotes de insumo (BOM).** Relação N:N — o sistema mantém o grafo completo de vínculos.                                     |
|RN-07|**Recall reverso:** dado um lote de insumo defeituoso, o sistema identifica todos os lotes de produto afetados.                                                         |

### 4.3 Perfis e Acesso

|ID   |Regra                                                                                                                                           |
|-----|------------------------------------------------------------------------------------------------------------------------------------------------|
|RN-08|**Dados financeiros são exclusivos do Produtor Premium.** Consultores, operadores e consumidores nunca acessam custos ou margens.               |
|RN-09|**Operador registra mas não consulta histórico completo.** Vê apenas o ciclo ativo e seus registros do turno.                                   |
|RN-10|**Certificador é vinculado à unidade produtiva, não ao agente.** Um auditor pode atender múltiplos clientes. Acesso revogado ao fim do contrato.|

### 4.4 Primata — Agente de IA

|ID   |Regra                                                                                                                 |
|-----|----------------------------------------------------------------------------------------------------------------------|
|RN-11|**Todo registro via Primata passa por confirmação humana antes de gravar.** Nunca grava automaticamente sem aprovação.|
|RN-12|**Timestamp do registro é o do dispositivo no momento da captura.** Não é o momento da sincronização.                 |

-----

## 5. Entidades de Negócio

### 5.1 Agente

Qualquer ator do sistema que interage com a plataforma.

|Atributo        |Tipo        |Constraint               |Descrição                        |
|----------------|------------|-------------------------|---------------------------------|
|`id`            |UUID        |PK, NOT NULL             |Identificador único imutável     |
|`nome`          |TEXT        |NOT NULL                 |Nome completo ou razão social    |
|`documento`     |TEXT        |NOT NULL, UNIQUE         |CPF ou CNPJ                      |
|`email`         |TEXT        |NOT NULL, UNIQUE         |Email de acesso                  |
|`tipo`          |ENUM        |NOT NULL                 |Ver `TipoAgente`                 |
|`plano`         |ENUM        |NOT NULL, DEFAULT `FREE` |Ver `PlanoAssinatura`            |
|`setor_primario`|TEXT        |NOT NULL                 |Template de setor padrão da conta|
|`ativo`         |BOOL        |NOT NULL, DEFAULT `true` |Conta ativa / suspensa           |
|`criado_em`     |TIMESTAMP TZ|NOT NULL, DEFAULT `now()`|Data de criação imutável         |
|`meta_json`     |JSONB       |DEFAULT `{}`             |Dados extensíveis por setor      |

**Relacionamentos:**

- 1 Agente → N UnidadeProdutiva
- 1 Agente → N PrimataSessao
- 1 Agente pode ser Certificador de N CicloProdutivo

-----

### 5.2 UnidadeProdutiva

Subdivisão operacional onde os processos ocorrem (talhão, linha, tear, ateliê).

|Atributo         |Tipo        |Constraint              |Descrição                       |
|-----------------|------------|------------------------|--------------------------------|
|`id`             |UUID        |PK, NOT NULL            |Identificador                   |
|`agente_id`      |UUID        |FK → Agente, NOT NULL   |Dono da unidade                 |
|`nome`           |TEXT        |NOT NULL                |Nome da unidade                 |
|`tipo`           |ENUM        |NOT NULL                |Ver `TipoUnidade`               |
|`area_capacidade`|DECIMAL     |NULLABLE                |Área (ha) ou capacidade (unid/h)|
|`lat`            |DECIMAL     |NULLABLE                |Latitude                        |
|`lng`            |DECIMAL     |NULLABLE                |Longitude                       |
|`setor_template` |TEXT        |NOT NULL                |Template de setor aplicado      |
|`ativo`          |BOOL        |NOT NULL, DEFAULT `true`|Ativa / inativa                 |
|`criado_em`      |TIMESTAMP TZ|NOT NULL                |Data de criação                 |

**Relacionamentos:**

- N UnidadeProdutiva → 1 Agente
- 1 UnidadeProdutiva → N CicloProdutivo

-----

### 5.3 ProtocoloProcesso

Template configurável que define as etapas obrigatórias e opcionais de um ciclo por setor.

|Atributo          |Tipo  |Constraint              |Descrição                                 |
|------------------|------|------------------------|------------------------------------------|
|`id`              |UUID  |PK, NOT NULL            |Identificador                             |
|`setor_template`  |TEXT  |NOT NULL                |Setor ao qual se aplica                   |
|`nome`            |TEXT  |NOT NULL                |Nome do protocolo (ex: “Café Especial v2”)|
|`versao`          |TEXT  |NOT NULL                |Versionamento semântico (ex: `2.1.0`)     |
|`etapas_json`     |JSONB |NOT NULL                |Array de etapas com nome, tipo e critérios|
|`etapas_obrig_ids`|UUID[]|NOT NULL                |IDs das etapas obrigatórias               |
|`ref_normativa`   |TEXT  |NULLABLE                |Referência normativa (ex: IN 51/2018)     |
|`ativo`           |BOOL  |NOT NULL, DEFAULT `true`|Protocolo ativo                           |

**Relacionamentos:**

- 1 ProtocoloProcesso → N CicloProdutivo

-----

### 5.4 CicloProdutivo

Período temporal de um processo completo — equivalente à safra, OP ou encomenda.

|Atributo      |Tipo        |Constraint                      |Descrição                  |
|--------------|------------|--------------------------------|---------------------------|
|`id`          |UUID        |PK, NOT NULL                    |Identificador              |
|`unidade_id`  |UUID        |FK → UnidadeProdutiva, NOT NULL |Onde ocorre o ciclo        |
|`protocolo_id`|UUID        |FK → ProtocoloProcesso, NOT NULL|Template de etapas aplicado|
|`codigo`      |TEXT        |NOT NULL, UNIQUE, IMMUTABLE     |Código gerado na criação   |
|`produto`     |TEXT        |NOT NULL                        |Nome do produto            |
|`status`      |ENUM        |NOT NULL, DEFAULT `ABERTO`      |Ver `StatusCiclo`          |
|`iniciado_em` |TIMESTAMP TZ|NOT NULL                        |Início do ciclo            |
|`encerrado_em`|TIMESTAMP TZ|NULLABLE                        |NULL enquanto aberto       |
|`insumos_json`|JSONB       |DEFAULT `[]`                    |Lista de insumos de entrada|
|`meta_json`   |JSONB       |DEFAULT `{}`                    |Dados específicos do setor |

**Relacionamentos:**

- N CicloProdutivo → 1 UnidadeProdutiva
- N CicloProdutivo → 1 ProtocoloProcesso
- 1 CicloProdutivo → N RegistroProcesso
- 1 CicloProdutivo → 1 Lote (após encerramento)
- N CicloProdutivo ↔ N Insumo (via CicloInsumo)

-----

### 5.5 RegistroProcesso

Evento imutável capturado durante o ciclo — operação, insumo, controle de qualidade ou anomalia.

|Atributo            |Tipo        |Constraint                       |Descrição                             |
|--------------------|------------|---------------------------------|--------------------------------------|
|`id`                |UUID        |PK, NOT NULL                     |Identificador                         |
|`ciclo_id`          |UUID        |FK → CicloProdutivo, NOT NULL    |Ciclo ao qual pertence                |
|`etapa_protocolo_id`|UUID        |FK → etapa do protocolo, NOT NULL|Etapa cumprida                        |
|`autor_agente_id`   |UUID        |FK → Agente, NOT NULL            |Quem registrou                        |
|`tipo_evento`       |ENUM        |NOT NULL                         |Ver `TipoEvento`                      |
|`descricao`         |TEXT        |NOT NULL                         |Descrição em linguagem natural        |
|`payload_json`      |JSONB       |NOT NULL, DEFAULT `{}`           |Dados estruturados do evento          |
|`status_validacao`  |ENUM        |NOT NULL, DEFAULT `PENDENTE`     |Ver `StatusValidacao`                 |
|`origem`            |ENUM        |NOT NULL                         |Ver `OrigemCaptura`                   |
|`capturado_em`      |TIMESTAMP TZ|NOT NULL, IMMUTABLE              |Timestamp do dispositivo — não do sync|
|`sincronizado_em`   |TIMESTAMP TZ|NULLABLE                         |Quando chegou ao backend              |
|`aditamento_de_id`  |UUID        |FK self, NULLABLE                |Se é correção: aponta para o original |
|`visivel_publico`   |BOOL        |NOT NULL, DEFAULT `true`         |`false` = oculto no QR                |

**Relacionamentos:**

- N RegistroProcesso → 1 CicloProdutivo
- N RegistroProcesso → 1 Agente (autor)
- 1 RegistroProcesso pode ser aditamento de 1 RegistroProcesso

-----

### 5.6 Lote

Agrupamento rastreável e imutável gerado ao final de um ciclo produtivo encerrado e validado.

|Atributo        |Tipo        |Constraint                           |Descrição                                |
|----------------|------------|-------------------------------------|-----------------------------------------|
|`id`            |UUID        |PK, NOT NULL                         |Identificador                            |
|`ciclo_id`      |UUID        |FK → CicloProdutivo, NOT NULL, UNIQUE|1:1 com ciclo                            |
|`codigo_lote`   |TEXT        |NOT NULL, UNIQUE, IMMUTABLE          |Código permanente — nunca reutilizado    |
|`qr_hash`       |TEXT        |NOT NULL, UNIQUE                     |Hash do QR Code — chave pública de acesso|
|`status`        |ENUM        |NOT NULL, DEFAULT `GERADO`           |Ver `StatusLote`                         |
|`gerado_em`     |TIMESTAMP TZ|NOT NULL, IMMUTABLE                  |Data de geração — nunca alterada         |
|`snapshot_json` |JSONB       |NOT NULL, IMMUTABLE                  |Cópia imutável do histórico completo     |
|`publico`       |BOOL        |NOT NULL, DEFAULT `false`            |Controla visibilidade do portal QR       |
|`cert_agente_id`|UUID        |FK → Agente, NULLABLE                |Consultor que validou e assinou          |

**Relacionamentos:**

- 1 Lote → 1 CicloProdutivo
- 1 Lote → N QrAcesso
- 1 Lote → 1 Agente (certificador, opcional)

-----

### 5.7 Insumo

Matéria-prima ou componente com rastreabilidade de origem e fornecedor.

|Atributo          |Tipo   |Constraint           |Descrição                               |
|------------------|-------|---------------------|----------------------------------------|
|`id`              |UUID   |PK, NOT NULL         |Identificador                           |
|`fornecedor_id`   |UUID   |FK → Agente, NULLABLE|Fornecedor (se também usa Di Mata)      |
|`codigo_lote_forn`|TEXT   |NULLABLE             |Lote do fornecedor para rastreio externo|
|`nome`            |TEXT   |NOT NULL             |Nome do insumo                          |
|`tipo_insumo`     |TEXT   |NOT NULL             |Categoria (semente, polímero, fio…)     |
|`quantidade`      |DECIMAL|NOT NULL             |Quantidade disponível                   |
|`unidade`         |TEXT   |NOT NULL             |Unidade de medida (kg, m, L…)           |
|`certificado_url` |TEXT   |NULLABLE             |URL do certificado do fornecedor        |

**Relacionamentos:**

- N Insumo ↔ N CicloProdutivo (via CicloInsumo)
- N Insumo → 1 Agente (fornecedor, opcional)

-----

### 5.8 CicloInsumo *(Junction)*

Tabela de associação N:N entre ciclos e insumos — permite BOM completo e recall reverso.

|Atributo          |Tipo        |Constraint                   |Descrição                              |
|------------------|------------|-----------------------------|---------------------------------------|
|`ciclo_id`        |UUID        |FK → CicloProdutivo, NOT NULL|Ciclo que consumiu o insumo            |
|`insumo_id`       |UUID        |FK → Insumo, NOT NULL        |Insumo consumido                       |
|`quantidade_usada`|DECIMAL     |NOT NULL                     |Quantidade efetivamente usada          |
|`registrado_em`   |TIMESTAMP TZ|NOT NULL                     |Quando foi registrado                  |
|`rastreado`       |BOOL        |NOT NULL, DEFAULT `false`    |Se o insumo tem rastreabilidade Di Mata|

**Chave primária composta:** `(ciclo_id, insumo_id)`

-----

### 5.9 PrimataSessao

Estado da sessão do agente de IA em campo — gerencia contexto, fila offline e sincronização.

|Atributo       |Tipo        |Constraint                   |Descrição                                       |
|---------------|------------|-----------------------------|------------------------------------------------|
|`id`           |UUID        |PK, NOT NULL                 |ID da sessão                                    |
|`agente_id`    |UUID        |FK → Agente, NOT NULL        |Quem iniciou a sessão                           |
|`ciclo_id`     |UUID        |FK → CicloProdutivo, NULLABLE|Ciclo ativo na sessão                           |
|`device_id`    |TEXT        |NOT NULL                     |Identificador único do dispositivo              |
|`estado`       |ENUM        |NOT NULL                     |Ver `EstadoAgente`                              |
|`contexto_json`|JSONB       |DEFAULT `{}`                 |Estado atual do agente                          |
|`offline_queue`|JSONB[]     |DEFAULT `[]`                 |Fila de eventos offline                         |
|`kb_setor`     |TEXT        |NOT NULL                     |Setor da base de conhecimento carregada         |
|`kb_hash`      |TEXT        |NOT NULL                     |Versão do KB — invalida cache local se diferente|
|`modelo_ia_ver`|TEXT        |NOT NULL                     |Versão do modelo de IA do Primata               |
|`iniciada_em`  |TIMESTAMP TZ|NOT NULL                     |Início da sessão                                |
|`ultimo_sync`  |TIMESTAMP TZ|NULLABLE                     |Última sincronização bem-sucedida               |

**Relacionamentos:**

- N PrimataSessao → 1 Agente
- N PrimataSessao → 1 CicloProdutivo (opcional)

-----

### 5.10 KbItem

Item da base de conhecimento do Primata — ontologia de termos por setor.

|Atributo         |Tipo  |Constraint             |Descrição                                |
|-----------------|------|-----------------------|-----------------------------------------|
|`id`             |UUID  |PK, NOT NULL           |Identificador                            |
|`setor`          |TEXT  |NOT NULL               |Setor ao qual pertence                   |
|`categoria`      |ENUM  |NOT NULL               |Ver `CategoriaKb`                        |
|`termo`          |TEXT  |NOT NULL               |Termo principal                          |
|`sinonimos`      |TEXT[]|DEFAULT `[]`           |Variações e sinônimos reconhecidos       |
|`descricao`      |TEXT  |NOT NULL               |Descrição do termo                       |
|`parametros_json`|JSONB |DEFAULT `{}`           |Parâmetros esperados ao capturar o evento|
|`confianca`      |FLOAT |NOT NULL, DEFAULT `1.0`|Nível de confiança do mapeamento (0–1)   |

-----

### 5.11 AuditoriaLog

Log imutável de todas as ações de criação, mudança de status e geração de lote.

|Atributo       |Tipo        |Constraint           |Descrição                                          |
|---------------|------------|---------------------|---------------------------------------------------|
|`id`           |UUID        |PK, NOT NULL         |Identificador                                      |
|`entidade_id`  |UUID        |NOT NULL             |ID da entidade afetada                             |
|`entidade_tipo`|TEXT        |NOT NULL             |Nome da tabela afetada                             |
|`ator_id`      |UUID        |FK → Agente, NOT NULL|Quem executou a ação                               |
|`acao`         |TEXT        |NOT NULL             |Ação executada (CREATE, STATUS_CHANGE, GERAR_LOTE…)|
|`dados_antes`  |JSONB       |NULLABLE             |Estado anterior                                    |
|`dados_depois` |JSONB       |NULLABLE             |Estado posterior                                   |
|`ip_origem`    |TEXT        |NULLABLE             |IP da requisição                                   |
|`ocorrido_em`  |TIMESTAMP TZ|NOT NULL             |Timestamp da ação                                  |

-----

### 5.12 QrAcesso

Registro de cada escaneamento do QR Code — analytics de alcance do lote.

|Atributo         |Tipo        |Constraint           |Descrição                  |
|-----------------|------------|---------------------|---------------------------|
|`id`             |UUID        |PK, NOT NULL         |Identificador              |
|`lote_id`        |UUID        |FK → Lote, NOT NULL  |Lote acessado              |
|`ip_origem`      |TEXT        |NULLABLE             |IP do consumidor           |
|`user_agent`     |TEXT        |NULLABLE             |Navegador / dispositivo    |
|`geo_json`       |JSONB       |NULLABLE             |Localização aproximada     |
|`acessado_em`    |TIMESTAMP TZ|NOT NULL             |Timestamp do acesso        |
|`patrocinador_id`|UUID        |FK → Agente, NULLABLE|Marca patrocinadora exibida|

-----

## 6. Enumerações e Tipos

```
TipoAgente:
  PRODUTOR_RURAL | INDUSTRIAL | ARTESAO | CONSULTOR_TECNICO
  | OPERADOR | CONSUMIDOR | ADMIN_PLATAFORMA

PlanoAssinatura:
  FREE | CORE_PLUS | PREMIUM_AGRO | INDUSTRIA_BASIC
  | INDUSTRIA_PRO | COOPERATIVA

TipoUnidade:
  TALHAO | LINHA_PRODUCAO | TEAR | ATELIE | BAIA | VIVEIRO | OUTRO

StatusCiclo:
  ABERTO → EM_PRODUCAO → ENCERRADO → VALIDANDO
  → LOTE_GERADO → ARQUIVADO

TipoEvento:
  ENTRADA_INSUMO | OPERACAO | CTRL_QUALIDADE | ANOMALIA
  | MOVIMENTACAO | COLHEITA | EXPEDICAO

StatusValidacao:
  PENDENTE | VALIDADO | INVALIDO | ADITADO

OrigemCaptura:
  VOZ | FOTO | QR_SCAN | MANUAL | API

StatusLote:
  GERADO | PUBLICADO | SUSPENSO | REVOGADO

EstadoAgente:
  OCIOSO | ESCUTANDO | PROCESSANDO | AGUARD_CONFIRM
  | SINCRONIZANDO | OFFLINE

CategoriaKb:
  INSUMO | OPERACAO | CONTROLE_QUALIDADE | ANOMALIA
  | COLHEITA | MOVIMENTACAO
```

-----

## 7. Modelo de Relacionamento (ERD Textual)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MODELO RELACIONAL                            │
│                     Di Mata × Primata — Core                       │
└─────────────────────────────────────────────────────────────────────┘

AGENTE ─────────────────────────────────────────────────────────────────
  │ 1
  │
  ├── N ─── UNIDADE_PRODUTIVA ──────────────────────────────────────────
  │             │ 1
  │             │
  │             └── N ─── CICLO_PRODUTIVO ─────────────────────────────
  │                           │ 1          \  N
  │                           │             └─── CICLO_INSUMO ──── N ── INSUMO
  │                           │                  (junction N:N)
  │                           ├── N ─── REGISTRO_PROCESSO
  │                           │             │ N
  │                           │             └── 1 ─── AGENTE (autor)
  │                           │
  │                           └── 1 ─── LOTE ──────────────────────────
  │                                         │ 1
  │                                         ├── N ─── QR_ACESSO
  │                                         └── 1? ── AGENTE (cert.)
  │
  ├── N ─── PRIMATA_SESSAO
  │             │ N
  │             └── 1? ── CICLO_PRODUTIVO (ativo na sessão)
  │
  └── * (audit) ─── AUDITORIA_LOG (entidade_id polimórfico)

PROTOCOLO_PROCESSO
  │ 1
  └── N ─── CICLO_PRODUTIVO

KB_ITEM (standalone — consultado pelo Primata via setor)
```

### 7.1 Cardinalidades Detalhadas

|Entidade A       |Cardinalidade|Entidade B      |Chave                                  |
|-----------------|-------------|----------------|---------------------------------------|
|Agente           |1 : N        |UnidadeProdutiva|`unidade_produtiva.agente_id`          |
|Agente           |1 : N        |PrimataSessao   |`primata_sessao.agente_id`             |
|Agente           |1 : N        |RegistroProcesso|`registro_processo.autor_agente_id`    |
|Agente           |1 : N        |Lote (cert.)    |`lote.cert_agente_id` (nullable)       |
|UnidadeProdutiva |1 : N        |CicloProdutivo  |`ciclo_produtivo.unidade_id`           |
|ProtocoloProcesso|1 : N        |CicloProdutivo  |`ciclo_produtivo.protocolo_id`         |
|CicloProdutivo   |1 : N        |RegistroProcesso|`registro_processo.ciclo_id`           |
|CicloProdutivo   |1 : 1        |Lote            |`lote.ciclo_id` (UNIQUE)               |
|CicloProdutivo   |N : N        |Insumo          |via `CicloInsumo`                      |
|Lote             |1 : N        |QrAcesso        |`qr_acesso.lote_id`                    |
|PrimataSessao    |N : 1        |CicloProdutivo  |`primata_sessao.ciclo_id` (nullable)   |
|RegistroProcesso |1 : 1        |RegistroProcesso|`aditamento_de_id` (self-ref, nullable)|

-----

## 8. Diagrama UML de Classes

```
┌──────────────────────────────────────────────────────────────────────┐
│ «entity»                                                             │
│ Agente                                                               │
├──────────────────────────────────────────────────────────────────────┤
│ + id: UUID                                                           │
│ + nome: string                                                       │
│ + documento: string [unique]                                         │
│ + email: string [unique]                                             │
│ + tipo: TipoAgente                                                   │
│ + plano: PlanoAssinatura                                             │
│ + setorPrimario: string                                              │
│ + ativo: boolean                                                     │
├──────────────────────────────────────────────────────────────────────┤
│ + getUnidades(): UnidadeProdutiva[]                                  │
│ + podeAcessar(recurso: string): boolean                              │
│ + ativar(): void                                                     │
│ + desativar(): void                                                  │
└──────────────────────────────────────────────────────────────────────┘
        1 ↑                              1 ↑
        │ (owner)                          │ (certificador)
        │ N                                │ N
┌───────────────────────┐        ┌────────────────────────┐
│ «entity»              │        │ «aggregate root»        │
│ UnidadeProdutiva      │        │ Lote [immutable]        │
├───────────────────────┤        ├────────────────────────┤
│ + id: UUID            │        │ + id: UUID              │
│ + agenteId: UUID [FK] │        │ + cicloId: UUID [FK]    │
│ + nome: string        │        │ + codigoLote: string    │
│ + tipo: TipoUnidade   │        │ + qrHash: string        │
│ + lat, lng: decimal   │        │ + status: StatusLote    │
│ + setorTemplate       │        │ + geradoEm: datetime    │
├───────────────────────┤        │ + snapshotJson: JSONB   │
│ + abrirCiclo()        │        │ + publico: boolean      │
│ + getCiclosAtivos()   │        ├────────────────────────┤
└───────────────────────┘        │ + publicar(): void      │
        1 │                       │ + getQrUrl(): string    │
          │ N                     │ + getPublicView(): DTO  │
┌─────────────────────────────┐  └────────────────────────┘
│ «aggregate root»             │           ↑ 1
│ CicloProdutivo               │           │ (gerado por)
├─────────────────────────────┤           │ 1
│ + id: UUID                   │  ─────────┘
│ + unidadeId: UUID [FK]       │
│ + protocoloId: UUID [FK]     │
│ + codigo: string [imutável]  │
│ + produto: string            │
│ + status: StatusCiclo        │
│ + iniciadoEm: datetime       │
│ + encerradoEm: datetime?     │
├─────────────────────────────┤
│ + adicionarRegistro()        │
│ + encerrar()                 │
│ + validarProtocolo()         │◄──── 1 ProtocoloProcesso
│ + gerarLote(): Lote          │
│ + getEtapasFaltantes()       │
│ + calcularCusto()            │
└─────────────────────────────┘
        1 │                  N ↕ (via CicloInsumo)
          │ N                        │
┌─────────────────────────┐  ┌──────────────────────┐
│ «value object»          │  │ «entity»              │
│ RegistroProcesso        │  │ Insumo                │
│ [immutable after valid] │  ├──────────────────────┤
├─────────────────────────┤  │ + id: UUID            │
│ + id: UUID              │  │ + fornecedorId: UUID? │
│ + cicloId: UUID [FK]    │  │ + nome: string        │
│ + etapaProtocoloId      │  │ + tipoInsumo: string  │
│ + autorAgenteId         │  │ + quantidade: decimal │
│ + tipoEvento: TipoEvento│  │ + unidade: string     │
│ + descricao: string     │  │ + certificadoUrl?     │
│ + payloadJson: JSONB    │  ├──────────────────────┤
│ + statusValidacao       │  │ + getCertificado()    │
│ + origem: OrigemCaptura │  └──────────────────────┘
│ + capturadoEm: datetime │
│ + visivelPublico: bool  │
├─────────────────────────┤
│ + validar()             │
│ + invalidar(motivo)     │
│ + aditar(): Registro    │
└─────────────────────────┘

┌─────────────────────────────────────┐
│ «ai agent / service»                │
│ PrimataSessao                       │
├─────────────────────────────────────┤
│ + id: UUID                          │
│ + agenteId: UUID [FK]               │
│ + cicloId: UUID? [FK]               │
│ + deviceId: string                  │
│ + estado: EstadoAgente              │
│ + contextoJson: JSONB               │
│ + offlineQueue: EventoCaptura[]     │
│ + kbSetor: string                   │
│ + kbHash: string                    │
│ + modeloIaVer: string               │
├─────────────────────────────────────┤
│ + capturarVoz(audio): Rascunho      │
│ + capturarFoto(img): Rascunho       │
│ + lerQR(hash): InsumoDTO            │
│ + confirmarRegistro(draft): Evento  │
│ + sincronizar(): SyncResult         │
│ + consultarKB(termo): KbItem[]      │
│ + sugerirProximaEtapa(): Etapa      │
└─────────────────────────────────────┘

┌──────────────────────────────┐
│ «configuration»              │
│ ProtocoloProcesso            │
├──────────────────────────────┤
│ + id: UUID                   │
│ + setorTemplate: string      │
│ + nome: string               │
│ + versao: string             │
│ + etapasJson: JSONB          │
│ + etapasObrigIds: UUID[]     │
│ + refNormativa: string?      │
│ + ativo: boolean             │
├──────────────────────────────┤
│ + getEtapasObrigatorias()    │
│ + validarCiclo(ciclo): bool  │
└──────────────────────────────┘

┌──────────────────────────────┐
│ «knowledge»                  │
│ KbItem                       │
├──────────────────────────────┤
│ + id: UUID                   │
│ + setor: string              │
│ + categoria: CategoriaKb     │
│ + termo: string              │
│ + sinonimos: string[]        │
│ + descricao: string          │
│ + parametrosJson: JSONB      │
│ + confianca: float           │
├──────────────────────────────┤
│ + match(input): float        │
│ + getParametros(): Param[]   │
└──────────────────────────────┘
```

-----

## 9. Fluxo Principal do Sistema

```
01  Agente Produtor  →  Cadastra conta, unidade e protocolo
                         Resultado: Perfil ativo, template configurado

02  Agente Produtor  →  Abre ciclo produtivo (safra / OP / encomenda)
                         Resultado: Ciclo em status ABERTO

03  Primata/Operador →  Captura entrada de insumo via QR ou voz
                         Resultado: Insumo rastreado vinculado ao ciclo

04  Primata/Operador →  Registra operações do processo (template do setor)
                         Resultado: Histórico crescente com timestamps

05  Primata/Operador →  Registra controle de qualidade / conformidade
                         Resultado: Aprovação ou não-conformidade vinculada

06  Certificador     →  Revisa registros, valida e assina o ciclo
                         Resultado: Ciclo validado, pronto para fechamento

07  Agente Produtor  →  Registra conclusão do ciclo
                         Resultado: Status → ENCERRADO

08  Di Mata (auto)   →  Valida protocolo completo (etapas obrigatórias)
                         Resultado: Erro se incompleto / prossegue se OK

09  Di Mata (auto)   →  Gera Lote com código único, QR e snapshot
                         Resultado: Lote em status PUBLICADO

10  Agente Produtor  →  Aplica QR na embalagem / NF / produto
                         Resultado: QR disponível para escaneamento

11  Consumidor       →  Escaneia QR → acessa portal público
                         Resultado: Histórico completo sem login
```

-----

## 10. Perfis de Acesso

|Perfil                |Rastreabilidade|Processos|Custos|Mão de Obra|Histórico Completo|Portal QR|
|----------------------|---------------|---------|------|-----------|------------------|---------|
|Produtor (Premium)    |✓ Total        |✓ Total  |✓     |✓          |✓                 |✓        |
|Produtor (Core)       |✓ Total        |✓ Total  |✗     |✗          |✓                 |✓        |
|Consultor Técnico     |✓ Total        |✓ Total  |✗     |✗          |✓                 |✓        |
|Operador / Trabalhador|✗              |✓ Parcial|✗     |✗          |✗                 |✗        |
|Consumidor            |✓ Público      |✓ Resumo |✗     |✗          |✗                 |✓        |
|Admin Plataforma      |✓ Total        |✓ Total  |✓     |✓          |✓                 |✓        |

-----

## 11. Módulos do Sistema

### Core Universal (todos os setores e planos)

|ID   |Módulo                            |Equivalente SISBOV                      |
|-----|----------------------------------|----------------------------------------|
|MC-01|Cadastro do Agente Produtor       |CAD/PRO                                 |
|MC-02|Cadastro da Unidade Produtiva     |ERAS                                    |
|MC-03|Protocolo Básico de Processo      |Protocolo Básico SISBOV                 |
|MC-04|Ciclo Produtivo                   |Período de rastreamento                 |
|MC-05|Registro de Processos e Insumos   |Registro de movimentação                |
|MC-06|Geração de Lote Rastreável + QR   |Identificação individual (brinco + chip)|
|MC-07|Portal Público do Consumidor      |BND pública                             |
|MC-08|Painel do Certificador / Consultor|Certificadora credenciada               |

### Módulos Industriais

|ID   |Módulo                              |Plano             |
|-----|------------------------------------|------------------|
|MI-01|Ordem de Produção (OP)              |Industrial Core   |
|MI-02|Rastreabilidade de Componentes / BOM|Industrial Core   |
|MI-03|Controle de Qualidade Inline        |Industrial Core   |
|MI-04|Rastreabilidade de Fornecedor       |Industrial Premium|
|MI-05|Gestão de Máquinas e Manutenção     |Industrial Premium|

### Módulos Primata (Agente de IA)

|ID   |Módulo                            |Plano       |
|-----|----------------------------------|------------|
|PA-01|Captura por Voz no Chão de Fábrica|Core Primata|
|PA-02|Leitura de QR / Código de Barras  |Core Primata|
|PA-03|Alerta de Gap de Processo         |Core Primata|
|PA-04|Modo Offline com Sync Segura      |Core Primata|

### Módulos Premium Agro

|ID   |Módulo                    |Plano       |
|-----|--------------------------|------------|
|PA-05|Gestão de Custos por Ciclo|Premium Agro|
|PA-06|Gestão de Mão de Obra     |Premium Agro|
|PA-07|Relatórios e Exportação   |Premium Agro|

-----

*Di Mata × Primata · Modelagem de Requisitos v2.0 · 2026*  
*Ref: SISBOV/MAPA · IN nº 51/2018 · IN nº 17/2006 · Decreto nº 7.623/2011*