# Clean Code Guidelines

## Objetivo

Manter o código:
- legível
- testável
- desacoplado
- previsível
- simples de evoluir

---

# Regras Gerais

## Prefira clareza sobre abstração

Evite:
- abstrações desnecessárias
- factories sem necessidade
- heranças complexas
- genericismo excessivo

Prefira:
- código explícito
- fluxo simples
- composição

---

# Controllers

Controllers devem:
- receber request
- validar entrada
- delegar para service
- retornar response

Controllers NÃO devem:
- conter regra de negócio
- acessar banco
- construir prompts
- chamar provider diretamente

---

# Services

Services devem:
- centralizar regra de negócio
- encapsular comportamento
- usar interfaces quando necessário

Evite:
- services gigantes
- múltiplas responsabilidades
- dependências cíclicas

---

# Configuração

Classes de configuração devem:
- conter apenas beans/config
- evitar lógica de negócio

---

# Integração com IA

Nunca:
- acoplar código ao provider
- espalhar prompts hardcoded
- misturar prompt com controller

Prefira:
- isolamento do provider
- prompts externalizados
- interfaces para IA

---

# Tratamento de Exceções

Sempre:
- usar exceptions específicas
- centralizar tratamento
- retornar mensagens claras

Nunca:
- retornar stacktrace ao usuário
- usar Exception genérica sem necessidade

---

# Logs

Logs devem:
- ajudar troubleshooting
- conter contexto útil

Nunca:
- logar tokens
- logar secrets
- logar dados sensíveis

---

# Testes

Priorizar:
- testes unitários
- testes de integração
- testes de configuração
- testes mutation
- testes de service
- testes de controller

Evitar:
- testes frágeis
- mocks excessivos
- dependência de serviços externos

---

# Métodos

Métodos devem:
- ter responsabilidade única
- nomes explícitos
- baixa complexidade

Evite:
- métodos longos
- muitos parâmetros
- efeitos colaterais ocultos

---

# Dependências

Prefira:
- constructor injection
- interfaces
- baixo acoplamento

Evite:
- new manual
- dependências concretas
- acoplamento entre camadas

---

# Arquitetura

Objetivos:
- modularidade
- baixo acoplamento
- facilidade de manutenção
- facilidade para testes
- facilidade para IA entender o código

---

# Convenções

## Nomes

Use nomes:
- claros
- sem abreviações confusas
- orientados ao domínio

---

# Código para IA

O código deve ser:
- fácil de navegar
- semanticamente claro
- previsível para agentes de IA

Evite:
- indireção excessiva
- meta-programação desnecessária
- estruturas muito fragmentadas