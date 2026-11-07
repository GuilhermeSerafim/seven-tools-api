# AGENTS.md — SEVEN Tools API

## O que e este repo

Backend do SEVEN Tools Hub. Expoe a API REST consumida pelo frontend, gerencia autenticacao, sessoes, persistencia e integracao com IA.

## Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x (async)
- Alembic (migrations)
- PostgreSQL
- pytest + httpx (testes)
- Groq API — llama-3.3-70b-versatile (IA)

## Estrutura principal

```
app/
  main.py              # entrada FastAPI
  config.py            # settings via env
  database.py          # engine e session SQLAlchemy
  dependencies.py      # deps de injecao
  models/              # modelos SQLAlchemy
  schemas/             # schemas Pydantic
  modules/
    auth/              # login, registro, sessao
    users/             # perfil e gestao de usuarios
    ai/                # proxy para Groq API
    proposals/         # criacao e evolucao de propostas
    lead_qualification/ # qualificacao de leads com score
  utils/
alembic/               # migrations
knowledge/caloni/      # knowledge base editorial do Metodo Caloni (runtime)
knowledge/naka/        # knowledge base editorial do Metodo Naka (runtime)
docs/context/          # contexto canonico de produto e ICP
tests/                 # pytest + httpx
```

## Contexto de produto

- Visao geral: `docs/context/00-product-context.md`
- ICP: `docs/context/10-icp-seven.md`

## Knowledge base

- `knowledge/caloni/*.md` — base editorial do Metodo Caloni
- `knowledge/naka/*.md` — base editorial do Metodo Naka

Ambas sao usadas em runtime pelas ferramentas de IA. Nao mover nem reestruturar sem alinhar com o time.

`app/modules/ai/knowledge.py` define `PROFILES` para carregar recortes de knowledge por contexto. O profile
`proposal_assistant` e usado pelo assistente unificado de proposta para reduzir tokens mantendo o contexto Caloni
necessario.

## IA e proposta comercial

- Endpoint ativo para o chat unificado: `POST /api/v1/ai/proposal-assistant`
- Esse endpoint orquestra criacao, edicao e validacao de propostas via tool-calling.
- A validacao deterministica roda internamente pelo tool call `request_validation`, reutilizando `validate_proposal_service`.
- Fluxos externos devem passar pelo proposal-assistant; validacao direta fica interna ao modulo de IA.

## Comandos

```bash
# servidor local
uvicorn app.main:app --reload

# testes
docker-compose up -d db  # PostgreSQL obrigatorio
pytest

# migrations
alembic upgrade head
alembic revision --autogenerate -m "descricao"

# lint
ruff check .
```

## Guardrails

- UUIDs como PK em todas as tabelas
- Sessions server-side com sliding expiration de 7 dias
- Testes sempre com PostgreSQL via Docker — nunca SQLite in-memory
- Nao expor endpoints sem autenticacao a menos que explicitamente pedido
- Nao alterar a knowledge base (Caloni ou Naka) sem contexto claro
