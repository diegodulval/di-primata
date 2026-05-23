# Filosofia Operacional do diAuto

O diAuto não é "ChatGPT para oficina" — é uma **camada operacional assistida**.

> **IA sugere. Humano confirma.**

---

## Os 4 Pilares

### 1. Delegation — Limites da automação

**A IA NÃO deve:**
- Emitir NF automaticamente sem confirmação
- Fechar orçamento sozinha
- Alterar estoque crítico sem revisão
- Aprovar compra ou decisão financeira
- Apagar histórico

**A IA DEVE:**
- Estruturar informação e reduzir digitação
- Sugerir ações e preencher rascunhos
- Resumir contexto e acelerar operação

**Fluxo correto:**
```
Entrada → Interpretação → Sugestão → Confirmação → Execução
```
Nunca `Entrada → Execução automática`.

---

### 2. Description — Comunicação natural

O mecânico não escreve prompt. O sistema interpreta **linguagem operacional informal**.

```
Mecânico: "gol prata voltou, barulho suspensão esquerda"

IA:
  → identifica veículo e cliente
  → abre retorno de OS
  → sugere histórico anterior
  → aguarda confirmação
```

O desafio real é **modelagem operacional**: peças, serviços, fluxo e linguagem de oficina.

---

### 3. Discernment — Confiança e rastreabilidade

Toda ação da IA deve mostrar claramente:

```
Entendi:
- veículo: Gol G5
- serviço: troca amortecedor dianteiro
- peças sugeridas: 2 amortecedores Monroe
- mão de obra estimada: R$ 180

Confirmar?
```

IA invisível (sem explicação do que fez e por quê) **quebra confiança rapidamente**.

---

### 4. Diligence — Responsabilidade e auditoria

Toda ação deve distinguir a origem:

| Origem | Exemplo de marcação |
|---|---|
| Digitado por humano | (sem marcação especial) |
| Inferido pela IA | `via IA — baseado em histórico` |
| Automatizado pelo sistema | `gerado automaticamente` |

Crítico em: NF, financeiro, histórico técnico, garantia, auditoria.

---

## Resumo dos pilares

| Pilar | Papel no produto |
|---|---|
| **Delegation** | Define os limites da automação |
| **Description** | Garante comunicação natural com o operador |
| **Discernment** | Constrói confiança via transparência |
| **Diligence** | Protege com rastreabilidade e responsabilidade |

---

## Regra de implementação

Antes de qualquer nova feature de IA, responder:

1. **Delegation:** Isso executa sozinho ou exige confirmação humana?
2. **Description:** O usuário consegue expressar isso em linguagem natural de oficina?
3. **Discernment:** O usuário consegue entender o que a IA fez e corrigir se errar?
4. **Diligence:** Existe rastro auditável de quem/o quê gerou essa ação?

Se algum dos quatro não estiver coberto, a feature não está pronta para produção.
