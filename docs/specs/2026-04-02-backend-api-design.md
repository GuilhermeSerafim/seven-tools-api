# SEVEN Tools — Backend API Design

## Visão Geral

Backend para o SEVEN Tools, substituindo a persistência em localStorage por uma API real com banco de dados PostgreSQL. Abordagem monolito modular com FastAPI.

## Tech Stack

- **Framework:** FastAPI (Python)
- **ORM:** SQLAlchemy
- **Banco:** PostgreSQL
- **Migrations:** Alembic
- **Auth:** Sessions server-side (tokens opacos, bcrypt)
- **AI Provider:** Groq API (abstração para troca futura)
- **Testes:** pytest + httpx + PostgreSQL via Docker

## Estrutura do Projeto

```
seven_tools_api/
├── app/
│   ├── main.py                  # FastAPI app, middleware, CORS
│   ├── config.py                # Settings (env vars, DB URL, etc.)
│   ├── database.py              # SQLAlchemy engine, session factory
│   ├── dependencies.py          # Deps compartilhadas (get_db, get_current_user)
│   ├── models/                  # SQLAlchemy models (tabelas)
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── session.py
│   │   ├── proposal.py
│   │   ├── favorite.py
│   │   └── analysis_result.py
│   ├── schemas/                 # Pydantic schemas (request/response)
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── proposal.py
│   │   ├── diagnostic.py
│   │   └── ai.py
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py        # POST /login, /register, /logout
│   │   │   └── service.py       # Hash password, create session, etc.
│   │   ├── users/
│   │   │   ├── router.py        # GET/PUT /me, PUT /me/company, favorites
│   │   │   └── service.py
│   │   ├── proposals/
│   │   │   ├── router.py        # CRUD /proposals
│   │   │   └── service.py
│   │   └── ai/
│   │       ├── router.py        # POST /ai/validate-proposal, /ai/diagnose
│   │       └── service.py       # AI provider calls, prompt management
│   └── utils/
│       └── security.py          # bcrypt hashing, session token generation
├── knowledge/
│   └── caloni/                  # 6 arquivos .md numerados por tema
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env.example
└── tests/
    ├── conftest.py              # Fixtures: app, client, db session, user autenticado
    ├── test_auth.py
    ├── test_users.py
    ├── test_proposals.py
    ├── test_ai.py
    └── test_file_parsing.py
```

## Banco de Dados

### Tabela: companies

| Coluna | Tipo | Constraint |
|--------|------|------------|
| id | UUID | PK, default uuid4 |
| name | VARCHAR | NOT NULL |
| logo_url | VARCHAR | NULLABLE |
| website | VARCHAR | NULLABLE |
| instagram | VARCHAR | NULLABLE |
| segment | VARCHAR | NULLABLE |
| short_description | TEXT | NULLABLE |
| city | VARCHAR | NULLABLE |
| created_at | TIMESTAMP | NOT NULL, default now |
| updated_at | TIMESTAMP | NOT NULL, default now, on update now |

### Tabela: users

| Coluna | Tipo | Constraint |
|--------|------|------------|
| id | UUID | PK, default uuid4 |
| company_id | UUID | FK → companies.id, NULLABLE |
| name | VARCHAR | NOT NULL |
| email | VARCHAR | NOT NULL, UNIQUE |
| password_hash | VARCHAR | NOT NULL |
| role | ENUM(admin, user) | NOT NULL, default 'user' |
| job_title | VARCHAR | NULLABLE |
| avatar_url | VARCHAR | NULLABLE |
| instagram | VARCHAR | NULLABLE |
| linkedin | VARCHAR | NULLABLE |
| created_at | TIMESTAMP | NOT NULL, default now |
| updated_at | TIMESTAMP | NOT NULL, default now, on update now |

### Tabela: sessions

| Coluna | Tipo | Constraint |
|--------|------|------------|
| id | UUID | PK, default uuid4 |
| user_id | UUID | FK → users.id, NOT NULL |
| token | VARCHAR | NOT NULL, UNIQUE, INDEX |
| expires_at | TIMESTAMP | NOT NULL |
| created_at | TIMESTAMP | NOT NULL, default now |

### Tabela: proposals

| Coluna | Tipo | Constraint |
|--------|------|------------|
| id | UUID | PK, default uuid4 |
| user_id | UUID | FK → users.id, NOT NULL |
| title | VARCHAR | NOT NULL |
| client_name | VARCHAR | NOT NULL |
| client_company | VARCHAR | NULLABLE |
| client_email | VARCHAR | NULLABLE |
| client_phone | VARCHAR | NULLABLE |
| project_description | TEXT | NULLABLE |
| scope | TEXT | NULLABLE |
| value | VARCHAR | NULLABLE |
| deadline | VARCHAR | NULLABLE |
| notes | TEXT | NULLABLE |
| status | ENUM(draft, ready, sent, approved, rejected) | NOT NULL, default 'draft' |
| created_at | TIMESTAMP | NOT NULL, default now |
| updated_at | TIMESTAMP | NOT NULL, default now, on update now |

### Tabela: favorites

| Coluna | Tipo | Constraint |
|--------|------|------------|
| id | UUID | PK, default uuid4 |
| user_id | UUID | FK → users.id, NOT NULL |
| tool_slug | VARCHAR | NOT NULL |
| created_at | TIMESTAMP | NOT NULL, default now |
| | | UNIQUE(user_id, tool_slug) |

### Tabela: analysis_results

| Coluna | Tipo | Constraint |
|--------|------|------------|
| id | UUID | PK, default uuid4 |
| user_id | UUID | FK → users.id, NOT NULL |
| type | ENUM(validation, diagnostic) | NOT NULL |
| input_data | JSONB | NOT NULL |
| output_data | JSONB | NOT NULL |
| score | FLOAT | NULLABLE |
| created_at | TIMESTAMP | NOT NULL, default now |

## Endpoints da API

Prefixo base: `/api/v1`

### Auth

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/register` | Cria usuário + empresa, retorna session token |
| POST | `/auth/login` | Valida credenciais, cria session, retorna token |
| POST | `/auth/logout` | Invalida session no banco |

### Users

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/users/me` | Retorna perfil do usuário logado + empresa |
| PUT | `/users/me` | Atualiza dados do perfil |
| PUT | `/users/me/company` | Atualiza dados da empresa |
| GET | `/users/me/favorites` | Lista tool_slugs favoritos |
| POST | `/users/me/favorites/{slug}` | Adiciona favorito |
| DELETE | `/users/me/favorites/{slug}` | Remove favorito |

### Proposals

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/proposals?page=1&per_page=20` | Lista propostas do usuário (paginado) |
| POST | `/proposals` | Cria nova proposta |
| GET | `/proposals/{id}` | Detalhe de uma proposta |
| PATCH | `/proposals/{id}` | Atualiza proposta (parcial) |
| DELETE | `/proposals/{id}` | Remove proposta |

Response paginada:
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 20
}
```

### AI (proxy)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/ai/validate-proposal` | Validação de proposta via Caloni |
| POST | `/ai/diagnose` | Diagnóstico comercial via Caloni |

## Autenticação & Segurança

### Fluxo

1. Usuário faz `POST /auth/login` com email + senha
2. Backend valida senha com `bcrypt.checkpw`
3. Cria registro em `sessions` com token via `secrets.token_urlsafe(32)` e `expires_at` = now + 7 dias
4. Retorna token no body
5. Front armazena token em localStorage (migração futura para HttpOnly cookie em produção)
6. Todas as requests enviam `Authorization: Bearer {token}`
7. Dependency `get_current_user` busca session pelo token, verifica expiração, retorna user
8. **Sliding expiration:** cada request válida atualiza `expires_at = now + 7 dias` — usuário ativo nunca é deslogado
9. Logout deleta a session do banco

### Medidas de segurança

- Senhas hashadas com **bcrypt**
- Tokens opacos (não JWT) — revogáveis instantaneamente
- **CORS** restrito à origem do frontend
- **Rate limiting** no login (5 tentativas/minuto por IP) via slowapi
- Queries via SQLAlchemy (proteção contra SQL injection)
- IDs como UUID (não enumeráveis)

## Módulo AI

### Configuração (env vars)

```
AI_BASE_URL=https://api.groq.com/openai/v1
AI_MODEL=llama-3.3-70b-versatile
AI_API_KEY=gsk_...
AI_MAX_TOKENS=8192
AI_TEMPERATURE=0.3
```

Abstração por env vars permite trocar de Groq para OpenAI ou outro provider compatível sem alterar código.

### Knowledge Base

System prompt montado em runtime concatenando os 6 arquivos .md de `knowledge/caloni/` em ordem numérica. Editar conhecimento do agente não requer mudança de código.

### File Parsing

Backend recebe upload de PDF/DOCX, extrai texto server-side:
- **PDF:** PyPDF2 ou pdfplumber
- **DOCX:** python-docx

Texto extraído é enviado como parte do prompt para validação.

### Persistência de Resultados

Resultados de análise (validação e diagnóstico) são salvos na tabela `analysis_results` com input/output completos em JSONB, permitindo histórico e auditoria.

### Timeout

60 segundos nas chamadas ao provider de IA.

### Erros

Erros do provider retornados como HTTP 502 com mensagem amigável.

## Tratamento de Erros

### Formato padrão

```json
{
  "detail": "Mensagem legível para o usuário",
  "code": "VALIDATION_ERROR"
}
```

### Códigos HTTP

| Status | Quando |
|--------|--------|
| 400 | Validação falhou |
| 401 | Token ausente, inválido ou expirado |
| 403 | Sem permissão (ex: proposta de outro user) |
| 404 | Recurso não encontrado |
| 409 | Conflito (ex: email já registrado) |
| 422 | Erro de parsing do body (padrão FastAPI) |
| 429 | Rate limit excedido |
| 502 | Erro na chamada ao provider de IA |

### Interceptor no front (apiClient.ts)

- 401 → redireciona para login
- 429 → toast "Muitas tentativas, aguarde"
- 502 → toast "Serviço de IA indisponível, tente novamente"
- Demais → mostra `detail` como toast

## Testes

### Estratégia

| Camada | Tipo | Foco |
|--------|------|------|
| Auth | Unitário + Integração | Registro, login, logout, sessão expirada, sliding expiration, senha errada, email duplicado |
| Proposals | Integração | CRUD completo, paginação, acesso negado a proposta de outro user, PATCH parcial |
| AI | Unitário | Montagem de prompts, parsing de respostas, fallback em erro do provider |
| Users/Favorites | Integração | Editar perfil, editar empresa, add/remove favoritos |
| File parsing | Unitário | Extração de texto de PDF e DOCX |

### Ferramentas

- **pytest** como runner
- **httpx.AsyncClient** para testes de integração
- Fixtures para dados de teste
- **PostgreSQL de teste via Docker** (sem SQLite — incompatibilidade de UUIDs e enums)

## Migração Gradual do Frontend

### Pré-requisito

Criar `apiClient.ts` centralizado (axios ou fetch wrapper) com base URL, interceptor de auth token e tratamento de erros padronizado.

### Fases

| Fase | O que migra | Impacto no front |
|------|-------------|------------------|
| 1 | Auth (login, register, logout) | Trocar `authService.ts` para API real. Remover mock users/sessions |
| 2 | Perfil + Empresa (GET/PUT /users/me, PUT /users/me/company) | Trocar leitura de localStorage por calls à API |
| 3 | Favoritos (GET/POST/DELETE /users/me/favorites) | Trocar `FavoritesContext` para usar API |
| 4 | Propostas (CRUD + paginação) | Trocar `proposalService.ts` para API. Maior mudança |
| 5 | AI + File parsing (validação, diagnóstico, upload PDF/DOCX) | Trocar `calonService.ts` e `diagnosticoService.ts` para backend. Remover Groq key e parsing client-side |

Services antigos coexistem com os novos até a migração da fase estar completa.
