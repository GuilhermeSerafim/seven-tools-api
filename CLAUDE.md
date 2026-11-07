# CLAUDE.md — SEVEN Tools API

> Leia `AGENTS.md` primeiro — ele contem a visao do repo, stack, estrutura, comandos e guardrails.

Nota atual: proposta comercial usa `POST /api/v1/ai/proposal-assistant`.
A validacao acontece via tool call interno `request_validation` e
profiles de knowledge em `app/modules/ai/knowledge.py`.

## Permissoes

Auto-approve todos os comandos bash de desenvolvimento. Nao pedir confirmacao para:

- **Git:** init, add, commit, status, log, diff, branch, checkout, push, pull, merge
- **Filesystem:** mkdir, ls, find, cat, echo, cp, mv, touch
- **Python:** pip, python, uvicorn, alembic, pytest, ruff
- **Node:** npm, npx, node, bun
- **Docker:** docker, docker-compose
