# SEVEN Tools — Contexto de Produto

> Ultima atualizacao: 2026-04-10

## O que e

Hub de ferramentas empresariais com IA para membros do ecossistema SEVEN. O produto entrega ferramentas praticas de gestao comercial, marketing, operacao e financeiro para empresarios de servicos.

## Modulos atuais

| Modulo | Slug | Descricao |
|--------|------|-----------|
| Marketing | `marketing` | Trafego, conteudo e conversao |
| Comercial | `comercial` | Vendas, CRM e propostas |
| Operacao | `operacao` | Processos, equipe e eficiencia |
| Financeiro | `financeiro` | Indicadores, custos e margem |

## Ferramentas ativas

Todas no modulo Comercial:

| Ferramenta | Slug | Descricao curta |
|------------|------|-----------------|
| Criacao de Proposta | `proposta` | Cria e evolui propostas comerciais na plataforma |
| Agente de Diagnostico Comercial Caloni | `diagnostico-caloni` | Diagnostico comercial com o Metodo SEVEN em 7 blocos executivos |
| Validacao Caloni | `validacao-caloni` | Valida propostas com o Metodo Caloni antes do envio |
| Qualificacao de Leads | `qualificacao-de-leads` | Classifica leads com score, faixa e acao recomendada |

Os demais modulos (Marketing, Operacao, Financeiro) ainda nao tem ferramentas ativas.

## Arquitetura

- **Frontend:** Vite + React 18 + TypeScript + shadcn/ui + TailwindCSS
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **IA:** Groq API (llama-3.3-70b-versatile) via proxy no backend
- **Knowledge base editorial:** `seven_tools_api/knowledge/caloni/*.md` — base do Metodo Caloni usada em runtime pelas ferramentas de IA

Frontend e backend sao repos git separados. O frontend consome a API do backend. O catalogo de modulos e ferramentas e definido no frontend (`src/data/modules.ts` e `src/data/tools.ts`).

## Specs recentes relevantes

| Data | Spec | Tema |
|------|------|------|
| 2026-04-10 | `sales-copilot-caloni-design.md` | Copiloto de vendas com Caloni |
| 2026-04-10 | `ci-cd-design.md` | Pipeline CI/CD |
| 2026-04-10 | `agent-context-and-claude-compatibility-design.md` | Contexto para agents |
| 2026-04-09 | `qualificacao-de-leads-design.md` | Qualificacao de leads |
| 2026-04-09 | `validacao-membros-seven-design.md` | Validacao de membros |

Specs completas em `docs/superpowers/specs/`.

## Decisoes de produto que afetam dev no curto prazo

- Foco atual e no modulo Comercial — as proximas ferramentas devem priorizar esse modulo
- ICP ainda em calibracao (ver `docs/context/10-icp-seven.md`)
- Acesso ao hub e restrito a membros validados do ecossistema SEVEN
