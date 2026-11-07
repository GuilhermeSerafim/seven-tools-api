# SEVEN Tools API

API FastAPI do hub de ferramentas SEVEN.

## Ritual local

### Pre-requisitos

- Python 3.12+
- Docker Desktop

### Primeira instalacao

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Subir dependencias locais

```powershell
docker compose up -d db db-test
```

### Aplicar migrations

```powershell
.venv\Scripts\Activate.ps1
alembic upgrade head
```

### Rodar a API

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Integracao ClickUp do cadastro

A lista de empresas do cadastro vem da lista `Carteira de clientes` no ClickUp. A API usa:

- `CLICKUP_API_TOKEN`: token ClickUp com acesso a lista
- `CLICKUP_CLIENTS_LIST_ID`: id numerico da lista de clientes
- endpoint fixo: `GET https://api.clickup.com/api/v2/list/{CLICKUP_CLIENTS_LIST_ID}/task`

O frontend nao usa token do ClickUp. Ele chama `VITE_API_BASE_URL + /companies/registration-options`, e o backend sincroniza a base local quando ela ainda esta vazia.

### Rodar testes

```powershell
docker compose up -d db db-test
.venv\Scripts\Activate.ps1
pytest -x -q
```

### Derrubar os bancos locais

```powershell
docker compose down
```


## Publicacao do codigo

Este repositorio publica uma copia independente do projeto de equipe SEVEN Tools, com autorizacao para o codigo e as bases comerciais. O historico original de desenvolvimento permanece preservado separadamente.

Configure suas proprias credenciais a partir de `.env.example`. Esta publicacao nao configura deploy nem conecta servicos de producao.

Repositorio complementar: [SEVEN Tools Frontend](https://github.com/GuilhermeSerafim/seven-tools-frontend).
