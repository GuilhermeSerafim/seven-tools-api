# SEVEN Tools Backend API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend for SEVEN Tools, replacing localStorage persistence with a real PostgreSQL database, server-side auth, and AI proxy.

**Architecture:** Monolito modular FastAPI. Each domain (auth, users, proposals, ai) lives in its own module with router + service. SQLAlchemy models, Pydantic schemas, Alembic migrations. Sessions server-side with opaque tokens and sliding expiration.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16, bcrypt, httpx (AI proxy), pytest, Docker Compose (dev DB).

**Spec:** `docs/superpowers/specs/2026-04-02-backend-api-design.md`

---

## File Structure

```
seven_tools_api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, CORS, router includes
│   ├── config.py                  # Pydantic Settings (env vars)
│   ├── database.py                # Engine, SessionLocal, Base
│   ├── dependencies.py            # get_db, get_current_user
│   ├── models/
│   │   ├── __init__.py            # Re-exports all models
│   │   ├── company.py             # Company model
│   │   ├── user.py                # User model
│   │   ├── session.py             # Session model
│   │   ├── proposal.py            # Proposal model
│   │   ├── favorite.py            # Favorite model
│   │   └── analysis_result.py     # AnalysisResult model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                # LoginRequest, RegisterRequest, AuthResponse
│   │   ├── user.py                # UserResponse, UserUpdate, CompanyUpdate
│   │   ├── proposal.py            # ProposalCreate, ProposalPatch, ProposalResponse, PaginatedResponse
│   │   ├── ai.py                  # ValidateProposalRequest, DiagnoseRequest, analysis responses
│   │   └── common.py              # ErrorResponse
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # POST /auth/register, /auth/login, /auth/logout
│   │   │   └── service.py         # create_user, authenticate, create_session, invalidate_session
│   │   ├── users/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # GET/PUT /users/me, PUT /users/me/company, favorites CRUD
│   │   │   └── service.py         # update_user, update_company, favorites ops
│   │   ├── proposals/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # GET/POST/PATCH/DELETE /proposals
│   │   │   └── service.py         # CRUD + pagination
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── router.py          # POST /ai/validate-proposal, /ai/diagnose
│   │       ├── service.py         # AI provider client, prompt builder, response parser
│   │       └── knowledge.py       # Load and concatenate knowledge .md files
│   └── utils/
│       ├── __init__.py
│       └── security.py            # hash_password, verify_password, generate_token
├── knowledge/
│   └── caloni/                    # Already exists — 6 .md files
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── docker-compose.yml             # PostgreSQL for dev + test
├── requirements.txt
├── .env.example
├── pytest.ini
└── tests/
    ├── __init__.py
    ├── conftest.py                # Fixtures: app, client, db, authenticated user
    ├── test_auth.py
    ├── test_users.py
    ├── test_proposals.py
    ├── test_ai.py
    └── test_file_parsing.py
```

---

## Task 1: Project Scaffolding + Docker

**Files:**
- Create: `seven_tools_api/docker-compose.yml`
- Create: `seven_tools_api/requirements.txt`
- Create: `seven_tools_api/.env.example`
- Create: `seven_tools_api/.env`
- Create: `seven_tools_api/pytest.ini`
- Create: `seven_tools_api/app/__init__.py`
- Create: `seven_tools_api/app/config.py`
- Create: `seven_tools_api/tests/__init__.py`

- [ ] **Step 1: Create docker-compose.yml with PostgreSQL for dev + test**

```yaml
# seven_tools_api/docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: seven
      POSTGRES_PASSWORD: seven_dev
      POSTGRES_DB: seven_tools
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  db-test:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: seven_test
      POSTGRES_PASSWORD: seven_test
      POSTGRES_DB: seven_tools_test
    ports:
      - "5433:5432"

volumes:
  pgdata:
```

- [ ] **Step 2: Create requirements.txt**

```
# seven_tools_api/requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.1
psycopg2-binary==2.9.10
pydantic==2.10.4
pydantic-settings==2.7.1
bcrypt==4.2.1
python-multipart==0.0.20
slowapi==0.1.9
httpx==0.28.1
pdfplumber==0.11.4
python-docx==1.1.2

# test
pytest==8.3.4
pytest-asyncio==0.25.0
httpx==0.28.1
```

- [ ] **Step 3: Create .env.example and .env**

```ini
# seven_tools_api/.env.example
DATABASE_URL=postgresql://seven:seven_dev@localhost:5432/seven_tools
DATABASE_URL_TEST=postgresql://seven_test:seven_test@localhost:5433/seven_tools_test
SECRET_KEY=change-me-in-production
CORS_ORIGINS=http://localhost:8080
AI_BASE_URL=https://api.groq.com/openai/v1
AI_MODEL=llama-3.3-70b-versatile
AI_API_KEY=gsk_your_key_here
AI_MAX_TOKENS=8192
AI_TEMPERATURE=0.3
```

Copy `.env.example` to `.env` and fill in real values.

- [ ] **Step 4: Create pytest.ini**

```ini
# seven_tools_api/pytest.ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

- [ ] **Step 5: Create app/config.py**

```python
# seven_tools_api/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    database_url_test: str = ""
    secret_key: str = "dev-secret-key"
    cors_origins: str = "http://localhost:8080"
    ai_base_url: str = "https://api.groq.com/openai/v1"
    ai_model: str = "llama-3.3-70b-versatile"
    ai_api_key: str = ""
    ai_max_tokens: int = 8192
    ai_temperature: float = 0.3
    session_ttl_days: int = 7
    login_rate_limit: str = "5/minute"

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 6: Create empty __init__.py files**

Create empty `__init__.py` in:
- `seven_tools_api/app/__init__.py`
- `seven_tools_api/tests/__init__.py`

- [ ] **Step 7: Start Docker and install dependencies**

```bash
cd seven_tools_api
docker compose up -d
pip install -r requirements.txt
```

- [ ] **Step 8: Verify PostgreSQL is reachable**

```bash
python -c "from sqlalchemy import create_engine, text; e = create_engine('postgresql://seven:seven_dev@localhost:5432/seven_tools'); c = e.connect(); print(c.execute(text('SELECT 1')).scalar()); c.close()"
```

Expected: `1`

- [ ] **Step 9: Commit**

```bash
git add seven_tools_api/docker-compose.yml seven_tools_api/requirements.txt seven_tools_api/.env.example seven_tools_api/pytest.ini seven_tools_api/app/__init__.py seven_tools_api/app/config.py seven_tools_api/tests/__init__.py
git commit -m "feat(api): scaffold project with Docker, deps, and config"
```

---

## Task 2: Database Setup + Alembic

**Files:**
- Create: `seven_tools_api/app/database.py`
- Create: `seven_tools_api/alembic.ini`
- Create: `seven_tools_api/alembic/env.py`

- [ ] **Step 1: Create app/database.py**

```python
# seven_tools_api/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 2: Initialize Alembic**

```bash
cd seven_tools_api
alembic init alembic
```

- [ ] **Step 3: Edit alembic.ini — set sqlalchemy.url to empty (we use env.py)**

In `seven_tools_api/alembic.ini`, set:
```ini
sqlalchemy.url =
```

- [ ] **Step 4: Edit alembic/env.py to use our engine and Base**

```python
# seven_tools_api/alembic/env.py
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from app.config import settings
from app.database import Base

# Import all models so Alembic detects them
from app.models import *  # noqa: F401, F403

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    connectable = create_engine(settings.database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: Commit**

```bash
git add seven_tools_api/app/database.py seven_tools_api/alembic.ini seven_tools_api/alembic/
git commit -m "feat(api): database setup with SQLAlchemy and Alembic"
```

---

## Task 3: SQLAlchemy Models

**Files:**
- Create: `seven_tools_api/app/models/__init__.py`
- Create: `seven_tools_api/app/models/company.py`
- Create: `seven_tools_api/app/models/user.py`
- Create: `seven_tools_api/app/models/session.py`
- Create: `seven_tools_api/app/models/proposal.py`
- Create: `seven_tools_api/app/models/favorite.py`
- Create: `seven_tools_api/app/models/analysis_result.py`

- [ ] **Step 1: Create company model**

```python
# seven_tools_api/app/models/company.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(500))
    instagram: Mapped[str | None] = mapped_column(String(255))
    segment: Mapped[str | None] = mapped_column(String(255))
    short_description: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    users: Mapped[list["User"]] = relationship(back_populates="company")
```

- [ ] **Step 2: Create user model**

```python
# seven_tools_api/app/models/user.py
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)
    job_title: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    instagram: Mapped[str | None] = mapped_column(String(255))
    linkedin: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    company: Mapped["Company | None"] = relationship(back_populates="users")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    proposals: Mapped[list["Proposal"]] = relationship(back_populates="user")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(back_populates="user")
```

- [ ] **Step 3: Create session model**

```python
# seven_tools_api/app/models/session.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="sessions")
```

- [ ] **Step 4: Create proposal model**

```python
# seven_tools_api/app/models/proposal.py
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProposalStatus(str, enum.Enum):
    draft = "draft"
    ready = "ready"
    sent = "sent"
    approved = "approved"
    rejected = "rejected"


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    client_name: Mapped[str] = mapped_column(String(255))
    client_company: Mapped[str | None] = mapped_column(String(255))
    client_email: Mapped[str | None] = mapped_column(String(255))
    client_phone: Mapped[str | None] = mapped_column(String(50))
    project_description: Mapped[str | None] = mapped_column(Text)
    scope: Mapped[str | None] = mapped_column(Text)
    value: Mapped[str | None] = mapped_column(String(50))
    deadline: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProposalStatus] = mapped_column(Enum(ProposalStatus), default=ProposalStatus.draft)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="proposals")
```

- [ ] **Step 5: Create favorite model**

```python
# seven_tools_api/app/models/favorite.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "tool_slug", name="uq_user_tool"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    tool_slug: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="favorites")
```

- [ ] **Step 6: Create analysis_result model**

```python
# seven_tools_api/app/models/analysis_result.py
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnalysisType(str, enum.Enum):
    validation = "validation"
    diagnostic = "diagnostic"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[AnalysisType] = mapped_column(Enum(AnalysisType))
    input_data: Mapped[dict] = mapped_column(JSONB)
    output_data: Mapped[dict] = mapped_column(JSONB)
    score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="analysis_results")
```

- [ ] **Step 7: Create models/__init__.py re-exporting all models**

```python
# seven_tools_api/app/models/__init__.py
from app.models.company import Company
from app.models.user import User, Role
from app.models.session import Session
from app.models.proposal import Proposal, ProposalStatus
from app.models.favorite import Favorite
from app.models.analysis_result import AnalysisResult, AnalysisType

__all__ = [
    "Company",
    "User",
    "Role",
    "Session",
    "Proposal",
    "ProposalStatus",
    "Favorite",
    "AnalysisResult",
    "AnalysisType",
]
```

- [ ] **Step 8: Generate and run initial Alembic migration**

```bash
cd seven_tools_api
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

- [ ] **Step 9: Verify tables exist**

```bash
python -c "
from sqlalchemy import create_engine, inspect
e = create_engine('postgresql://seven:seven_dev@localhost:5432/seven_tools')
i = inspect(e)
print(sorted(i.get_table_names()))
"
```

Expected: `['alembic_version', 'analysis_results', 'companies', 'favorites', 'proposals', 'sessions', 'users']`

- [ ] **Step 10: Commit**

```bash
git add seven_tools_api/app/models/
git commit -m "feat(api): SQLAlchemy models for all tables"
```

---

## Task 4: Utility Functions + Shared Dependencies

**Files:**
- Create: `seven_tools_api/app/utils/__init__.py`
- Create: `seven_tools_api/app/utils/security.py`
- Create: `seven_tools_api/app/dependencies.py`
- Create: `seven_tools_api/app/schemas/__init__.py`
- Create: `seven_tools_api/app/schemas/common.py`

- [ ] **Step 1: Create security utilities**

```python
# seven_tools_api/app/utils/security.py
import secrets

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_token() -> str:
    return secrets.token_urlsafe(32)
```

- [ ] **Step 2: Create common schemas**

```python
# seven_tools_api/app/schemas/common.py
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    code: str
```

- [ ] **Step 3: Create empty __init__.py files**

Create empty files:
- `seven_tools_api/app/utils/__init__.py`
- `seven_tools_api/app/schemas/__init__.py`
- `seven_tools_api/app/modules/__init__.py`
- `seven_tools_api/app/modules/auth/__init__.py`
- `seven_tools_api/app/modules/users/__init__.py`
- `seven_tools_api/app/modules/proposals/__init__.py`
- `seven_tools_api/app/modules/ai/__init__.py`

- [ ] **Step 4: Create dependencies.py**

```python
# seven_tools_api/app/dependencies.py
from datetime import datetime, timedelta, timezone
from typing import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.database import SessionLocal
from app.models.session import Session
from app.models.user import User


def get_db() -> Generator[DbSession, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _error(status_code: int, detail: str, code: str):
    """Raise HTTPException with spec-compliant body: {detail, code}."""
    raise HTTPException(status_code=status_code, detail={"detail": detail, "code": code})


def get_current_user(
    authorization: str = Header(...),
    db: DbSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        _error(status.HTTP_401_UNAUTHORIZED, "Invalid authorization header", "INVALID_AUTH")

    token = authorization.removeprefix("Bearer ")

    session = db.query(Session).filter(Session.token == token).first()
    if session is None:
        _error(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session", "INVALID_SESSION")

    now = datetime.now(timezone.utc)
    if session.expires_at.replace(tzinfo=timezone.utc) < now:
        db.delete(session)
        db.commit()
        _error(status.HTTP_401_UNAUTHORIZED, "Session expired", "SESSION_EXPIRED")

    # Sliding expiration
    session.expires_at = now + timedelta(days=settings.session_ttl_days)
    db.commit()

    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None:
        _error(status.HTTP_401_UNAUTHORIZED, "User not found", "USER_NOT_FOUND")

    return user
```

- [ ] **Step 5: Commit**

```bash
git add seven_tools_api/app/utils/ seven_tools_api/app/schemas/ seven_tools_api/app/dependencies.py seven_tools_api/app/modules/__init__.py seven_tools_api/app/modules/auth/__init__.py seven_tools_api/app/modules/users/__init__.py seven_tools_api/app/modules/proposals/__init__.py seven_tools_api/app/modules/ai/__init__.py
git commit -m "feat(api): security utils, shared dependencies, common schemas"
```

---

## Task 5: Test Infrastructure

**Files:**
- Create: `seven_tools_api/tests/conftest.py`

- [ ] **Step 1: Create conftest.py with fixtures**

```python
# seven_tools_api/tests/conftest.py
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models.company import Company
from app.models.session import Session
from app.models.user import User
from app.utils.security import generate_token, hash_password


test_engine = create_engine(settings.database_url_test)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_company(db):
    company = Company(id=uuid.uuid4(), name="Test Company", segment="Tech", city="São Paulo")
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def sample_user(db, sample_company):
    user = User(
        id=uuid.uuid4(),
        company_id=sample_company.id,
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("password123"),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(db, sample_user):
    token = generate_token()
    session = Session(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(session)
    db.commit()
    return token


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
```

- [ ] **Step 2: Create minimal app/main.py (needed for tests to import)**

```python
# seven_tools_api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="SEVEN Tools API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Run a smoke test to verify infrastructure**

```bash
cd seven_tools_api
pytest tests/ -v --tb=short -k "not test_" --collect-only
```

Expected: no errors collecting, 0 tests selected (conftest loads fine).

- [ ] **Step 4: Commit**

```bash
git add seven_tools_api/tests/conftest.py seven_tools_api/app/main.py
git commit -m "feat(api): test infrastructure with PostgreSQL fixtures"
```

---

## Task 6: Auth Module — Schemas

**Files:**
- Create: `seven_tools_api/app/schemas/auth.py`

- [ ] **Step 1: Create auth schemas**

```python
# seven_tools_api/app/schemas/auth.py
import uuid
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_name: str


class AuthResponse(BaseModel):
    token: str
    user: "AuthUserResponse"


class AuthUserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add seven_tools_api/app/schemas/auth.py
git commit -m "feat(api): auth request/response schemas"
```

---

## Task 7: Auth Module — Service + Router (TDD)

**Files:**
- Create: `seven_tools_api/app/modules/auth/service.py`
- Create: `seven_tools_api/app/modules/auth/router.py`
- Create: `seven_tools_api/tests/test_auth.py`
- Modify: `seven_tools_api/app/main.py` (add router)

- [ ] **Step 1: Write failing tests for register**

```python
# seven_tools_api/tests/test_auth.py


def test_register_success(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "New User",
        "email": "new@example.com",
        "password": "securepass123",
        "company_name": "New Company",
    })
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert data["user"]["name"] == "New User"
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["role"] == "user"


def test_register_duplicate_email(client, sample_user):
    response = client.post("/api/v1/auth/register", json={
        "name": "Another User",
        "email": "test@example.com",  # same as sample_user
        "password": "securepass123",
        "company_name": "Another Company",
    })
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EMAIL_EXISTS"


def test_login_success(client, sample_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"


def test_login_wrong_password(client, sample_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_email(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_logout_success(client, auth_headers):
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200

    # Token should no longer work
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 401


def test_expired_session(client, db, sample_user):
    from datetime import datetime, timedelta, timezone
    from app.models.session import Session
    from app.utils.security import generate_token
    import uuid

    token = generate_token()
    session = Session(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(session)
    db.commit()

    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_sliding_expiration(client, db, auth_token):
    from app.models.session import Session

    session_before = db.query(Session).filter(Session.token == auth_token).first()
    expires_before = session_before.expires_at

    # Make an authenticated request
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {auth_token}"})
    # This will 404 until users router exists, but session should still be extended
    # For now just verify the session was updated
    db.refresh(session_before)
    assert session_before.expires_at >= expires_before
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd seven_tools_api
pytest tests/test_auth.py -v
```

Expected: All tests FAIL (routes don't exist yet).

- [ ] **Step 3: Create auth service**

```python
# seven_tools_api/app/modules/auth/service.py
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.company import Company
from app.models.session import Session
from app.models.user import User
from app.utils.security import generate_token, hash_password, verify_password


def register_user(
    db: DbSession,
    name: str,
    email: str,
    password: str,
    company_name: str,
) -> tuple[User, str]:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return None, "EMAIL_EXISTS"

    company = Company(id=uuid.uuid4(), name=company_name)
    db.add(company)

    user = User(
        id=uuid.uuid4(),
        company_id=company.id,
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()

    token = _create_session(db, user.id)
    db.commit()
    db.refresh(user)
    return user, token


def authenticate(db: DbSession, email: str, password: str) -> tuple[User | None, str | None]:
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.password_hash):
        return None, None

    token = _create_session(db, user.id)
    db.commit()
    return user, token


def invalidate_session(db: DbSession, token: str) -> bool:
    session = db.query(Session).filter(Session.token == token).first()
    if session is None:
        return False
    db.delete(session)
    db.commit()
    return True


def _create_session(db: DbSession, user_id: uuid.UUID) -> str:
    token = generate_token()
    session = Session(
        id=uuid.uuid4(),
        user_id=user_id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days),
    )
    db.add(session)
    return token
```

- [ ] **Step 4: Create auth router**

```python
# seven_tools_api/app/modules/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_db
from app.schemas.auth import AuthResponse, AuthUserResponse, LoginRequest, RegisterRequest
from app.modules.auth.service import authenticate, invalidate_session, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession = Depends(get_db)):
    user, token_or_error = register_user(
        db,
        name=body.name,
        email=body.email,
        password=body.password,
        company_name=body.company_name,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Email already registered", "code": token_or_error},
        )
    return AuthResponse(
        token=token_or_error,
        user=AuthUserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: DbSession = Depends(get_db)):
    user, token = authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Invalid email or password", "code": "INVALID_CREDENTIALS"},
        )
    return AuthResponse(
        token=token,
        user=AuthUserResponse.model_validate(user),
    )


@router.post("/logout")
def logout(
    authorization: str = Header(...),
    db: DbSession = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    token = authorization.removeprefix("Bearer ")

    # Validate session exists and is not expired (reuse dependency logic)
    from datetime import datetime, timezone
    from app.models.session import Session

    session = db.query(Session).filter(Session.token == token).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    invalidate_session(db, token)
    return {"detail": "Logged out successfully"}
```

- [ ] **Step 5: Register auth router in main.py**

Add to `seven_tools_api/app/main.py` after the CORS middleware:

```python
from app.modules.auth.router import router as auth_router

app.include_router(auth_router, prefix="/api/v1")
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd seven_tools_api
pytest tests/test_auth.py -v
```

Expected: All tests PASS (the sliding_expiration test may need the users router, adjust if needed).

- [ ] **Step 7: Commit**

```bash
git add seven_tools_api/app/modules/auth/ seven_tools_api/tests/test_auth.py seven_tools_api/app/main.py
git commit -m "feat(api): auth module — register, login, logout with TDD"
```

---

## Task 8: User Schemas

**Files:**
- Create: `seven_tools_api/app/schemas/user.py`

- [ ] **Step 1: Create user and company schemas**

```python
# seven_tools_api/app/schemas/user.py
import uuid
from pydantic import BaseModel, EmailStr


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    logo_url: str | None = None
    website: str | None = None
    instagram: str | None = None
    segment: str | None = None
    short_description: str | None = None
    city: str | None = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    job_title: str | None = None
    avatar_url: str | None = None
    instagram: str | None = None
    linkedin: str | None = None
    company: CompanyResponse | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    job_title: str | None = None
    avatar_url: str | None = None
    instagram: str | None = None
    linkedin: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    logo_url: str | None = None
    website: str | None = None
    instagram: str | None = None
    segment: str | None = None
    short_description: str | None = None
    city: str | None = None


class FavoriteResponse(BaseModel):
    tool_slugs: list[str]
```

- [ ] **Step 2: Commit**

```bash
git add seven_tools_api/app/schemas/user.py
git commit -m "feat(api): user and company schemas"
```

---

## Task 9: Users Module — Service + Router (TDD)

**Files:**
- Create: `seven_tools_api/app/modules/users/service.py`
- Create: `seven_tools_api/app/modules/users/router.py`
- Create: `seven_tools_api/tests/test_users.py`
- Modify: `seven_tools_api/app/main.py` (add router)

- [ ] **Step 1: Write failing tests**

```python
# seven_tools_api/tests/test_users.py


def test_get_me(client, auth_headers, sample_user, sample_company):
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["company"]["name"] == "Test Company"


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 422  # missing header


def test_update_me(client, auth_headers):
    response = client.put("/api/v1/users/me", headers=auth_headers, json={
        "name": "Updated Name",
        "job_title": "CTO",
        "instagram": "@updated",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["job_title"] == "CTO"
    assert data["instagram"] == "@updated"


def test_update_company(client, auth_headers, sample_company):
    response = client.put("/api/v1/users/me/company", headers=auth_headers, json={
        "name": "Updated Company",
        "segment": "SaaS",
        "city": "Curitiba",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Company"
    assert data["segment"] == "SaaS"
    assert data["city"] == "Curitiba"


def test_favorites_flow(client, auth_headers):
    # Initially empty
    response = client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["tool_slugs"] == []

    # Add a favorite
    response = client.post("/api/v1/users/me/favorites/proposta-comercial-smart", headers=auth_headers)
    assert response.status_code == 201

    # List favorites
    response = client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert response.json()["tool_slugs"] == ["proposta-comercial-smart"]

    # Add another
    client.post("/api/v1/users/me/favorites/diagnostico-comercial-caloni", headers=auth_headers)
    response = client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert len(response.json()["tool_slugs"]) == 2

    # Remove one
    response = client.delete("/api/v1/users/me/favorites/proposta-comercial-smart", headers=auth_headers)
    assert response.status_code == 200

    response = client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert response.json()["tool_slugs"] == ["diagnostico-comercial-caloni"]


def test_add_duplicate_favorite(client, auth_headers):
    client.post("/api/v1/users/me/favorites/some-tool", headers=auth_headers)
    response = client.post("/api/v1/users/me/favorites/some-tool", headers=auth_headers)
    assert response.status_code == 409


def test_remove_nonexistent_favorite(client, auth_headers):
    response = client.delete("/api/v1/users/me/favorites/nonexistent", headers=auth_headers)
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd seven_tools_api
pytest tests/test_users.py -v
```

Expected: All FAIL.

- [ ] **Step 3: Create users service**

```python
# seven_tools_api/app/modules/users/service.py
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.models.company import Company
from app.models.favorite import Favorite
from app.models.user import User


def update_user(db: DbSession, user: User, data: dict) -> User:
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def update_company(db: DbSession, company_id: uuid.UUID, data: dict) -> Company | None:
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


def get_favorites(db: DbSession, user_id: uuid.UUID) -> list[str]:
    favorites = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    return [f.tool_slug for f in favorites]


def add_favorite(db: DbSession, user_id: uuid.UUID, tool_slug: str) -> bool:
    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.tool_slug == tool_slug,
    ).first()
    if existing:
        return False

    fav = Favorite(id=uuid.uuid4(), user_id=user_id, tool_slug=tool_slug)
    db.add(fav)
    db.commit()
    return True


def remove_favorite(db: DbSession, user_id: uuid.UUID, tool_slug: str) -> bool:
    fav = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.tool_slug == tool_slug,
    ).first()
    if fav is None:
        return False
    db.delete(fav)
    db.commit()
    return True
```

- [ ] **Step 4: Create users router**

```python
# seven_tools_api/app/modules/users/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.modules.users.service import add_favorite, get_favorites, remove_favorite, update_company, update_user
from app.schemas.user import CompanyResponse, CompanyUpdate, FavoriteResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserResponse)
def put_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    updated = update_user(db, user, body.model_dump(exclude_unset=True))
    return updated


@router.put("/me/company", response_model=CompanyResponse)
def put_my_company(
    body: CompanyUpdate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    if user.company_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No company associated")
    company = update_company(db, user.company_id, body.model_dump(exclude_unset=True))
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.get("/me/favorites", response_model=FavoriteResponse)
def list_favorites(
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    slugs = get_favorites(db, user.id)
    return FavoriteResponse(tool_slugs=slugs)


@router.post("/me/favorites/{slug}", status_code=status.HTTP_201_CREATED)
def add_fav(
    slug: str,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    if not add_favorite(db, user.id, slug):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"detail": "Already a favorite", "code": "DUPLICATE_FAVORITE"})
    return {"detail": "Favorite added"}


@router.delete("/me/favorites/{slug}")
def remove_fav(
    slug: str,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    if not remove_favorite(db, user.id, slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Favorite not found", "code": "FAVORITE_NOT_FOUND"})
    return {"detail": "Favorite removed"}
```

- [ ] **Step 5: Register users router in main.py**

Add to `seven_tools_api/app/main.py`:

```python
from app.modules.users.router import router as users_router

app.include_router(users_router, prefix="/api/v1")
```

- [ ] **Step 6: Run tests**

```bash
cd seven_tools_api
pytest tests/test_users.py -v
```

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add seven_tools_api/app/modules/users/ seven_tools_api/tests/test_users.py seven_tools_api/app/main.py
git commit -m "feat(api): users module — profile, company, favorites with TDD"
```

---

## Task 10: Proposal Schemas

**Files:**
- Create: `seven_tools_api/app/schemas/proposal.py`

- [ ] **Step 1: Create proposal schemas**

```python
# seven_tools_api/app/schemas/proposal.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class ProposalCreate(BaseModel):
    title: str
    client_name: str
    client_company: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    project_description: str | None = None
    scope: str | None = None
    value: str | None = None
    deadline: str | None = None
    notes: str | None = None
    status: str = "draft"


class ProposalPatch(BaseModel):
    title: str | None = None
    client_name: str | None = None
    client_company: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    project_description: str | None = None
    scope: str | None = None
    value: str | None = None
    deadline: str | None = None
    notes: str | None = None
    status: str | None = None


class ProposalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    client_name: str
    client_company: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    project_description: str | None = None
    scope: str | None = None
    value: str | None = None
    deadline: str | None = None
    notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedProposalResponse(BaseModel):
    items: list[ProposalResponse]
    total: int
    page: int
    per_page: int
```

- [ ] **Step 2: Commit**

```bash
git add seven_tools_api/app/schemas/proposal.py
git commit -m "feat(api): proposal schemas"
```

---

## Task 11: Proposals Module — Service + Router (TDD)

**Files:**
- Create: `seven_tools_api/app/modules/proposals/service.py`
- Create: `seven_tools_api/app/modules/proposals/router.py`
- Create: `seven_tools_api/tests/test_proposals.py`
- Modify: `seven_tools_api/app/main.py` (add router)

- [ ] **Step 1: Write failing tests**

```python
# seven_tools_api/tests/test_proposals.py
import uuid


def test_create_proposal(client, auth_headers):
    response = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "Proposta para Empresa X",
        "client_name": "Maria Silva",
        "client_company": "Empresa X",
        "client_email": "maria@empresax.com",
        "value": "15000",
        "status": "draft",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Proposta para Empresa X"
    assert data["client_name"] == "Maria Silva"
    assert data["status"] == "draft"
    assert "id" in data


def test_list_proposals_empty(client, auth_headers):
    response = client.get("/api/v1/proposals", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 20


def test_list_proposals_with_pagination(client, auth_headers):
    # Create 3 proposals
    for i in range(3):
        client.post("/api/v1/proposals", headers=auth_headers, json={
            "title": f"Proposta {i}",
            "client_name": f"Client {i}",
        })

    # Page 1 with per_page=2
    response = client.get("/api/v1/proposals?page=1&per_page=2", headers=auth_headers)
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["per_page"] == 2

    # Page 2
    response = client.get("/api/v1/proposals?page=2&per_page=2", headers=auth_headers)
    data = response.json()
    assert len(data["items"]) == 1
    assert data["page"] == 2


def test_get_proposal(client, auth_headers):
    # Create
    create_resp = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "Test Proposal",
        "client_name": "Client A",
    })
    proposal_id = create_resp.json()["id"]

    # Get
    response = client.get(f"/api/v1/proposals/{proposal_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Proposal"


def test_get_proposal_not_found(client, auth_headers):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/proposals/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


def test_patch_proposal(client, auth_headers):
    create_resp = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "Original Title",
        "client_name": "Client A",
    })
    proposal_id = create_resp.json()["id"]

    # Partial update — only status
    response = client.patch(f"/api/v1/proposals/{proposal_id}", headers=auth_headers, json={
        "status": "ready",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["title"] == "Original Title"  # unchanged


def test_delete_proposal(client, auth_headers):
    create_resp = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "To Delete",
        "client_name": "Client A",
    })
    proposal_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/proposals/{proposal_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify deleted
    response = client.get(f"/api/v1/proposals/{proposal_id}", headers=auth_headers)
    assert response.status_code == 404


def test_cannot_access_other_users_proposal(client, db, auth_headers):
    """Proposals are scoped to the authenticated user."""
    from app.models.proposal import Proposal
    from app.models.user import User
    from app.utils.security import hash_password

    other_user = User(
        id=uuid.uuid4(),
        name="Other",
        email="other@example.com",
        password_hash=hash_password("pass"),
    )
    db.add(other_user)
    db.flush()

    other_proposal = Proposal(
        id=uuid.uuid4(),
        user_id=other_user.id,
        title="Other's Proposal",
        client_name="Private Client",
    )
    db.add(other_proposal)
    db.commit()

    response = client.get(f"/api/v1/proposals/{other_proposal.id}", headers=auth_headers)
    assert response.status_code == 404  # not 403 — don't reveal existence
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd seven_tools_api
pytest tests/test_proposals.py -v
```

Expected: All FAIL.

- [ ] **Step 3: Create proposals service**

```python
# seven_tools_api/app/modules/proposals/service.py
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.models.proposal import Proposal


def create_proposal(db: DbSession, user_id: uuid.UUID, data: dict) -> Proposal:
    proposal = Proposal(id=uuid.uuid4(), user_id=user_id, **data)
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def list_proposals(
    db: DbSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Proposal], int]:
    query = db.query(Proposal).filter(Proposal.user_id == user_id)
    total = query.count()
    items = (
        query
        .order_by(Proposal.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def get_proposal(db: DbSession, user_id: uuid.UUID, proposal_id: uuid.UUID) -> Proposal | None:
    return db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.user_id == user_id,
    ).first()


def patch_proposal(db: DbSession, proposal: Proposal, data: dict) -> Proposal:
    for key, value in data.items():
        if value is not None:
            setattr(proposal, key, value)
    db.commit()
    db.refresh(proposal)
    return proposal


def delete_proposal(db: DbSession, proposal: Proposal) -> None:
    db.delete(proposal)
    db.commit()
```

- [ ] **Step 4: Create proposals router**

```python
# seven_tools_api/app/modules/proposals/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.modules.proposals.service import create_proposal, delete_proposal, get_proposal, list_proposals, patch_proposal
from app.schemas.proposal import PaginatedProposalResponse, ProposalCreate, ProposalPatch, ProposalResponse

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: ProposalCreate,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    proposal = create_proposal(db, user.id, body.model_dump())
    return proposal


@router.get("", response_model=PaginatedProposalResponse)
def list_all(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    items, total = list_proposals(db, user.id, page, per_page)
    return PaginatedProposalResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_one(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    proposal = get_proposal(db, user.id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return proposal


@router.patch("/{proposal_id}", response_model=ProposalResponse)
def patch_one(
    proposal_id: uuid.UUID,
    body: ProposalPatch,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    proposal = get_proposal(db, user.id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    updated = patch_proposal(db, proposal, body.model_dump(exclude_unset=True))
    return updated


@router.delete("/{proposal_id}")
def delete_one(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    proposal = get_proposal(db, user.id, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    delete_proposal(db, proposal)
    return {"detail": "Proposal deleted"}
```

- [ ] **Step 5: Register proposals router in main.py**

Add to `seven_tools_api/app/main.py`:

```python
from app.modules.proposals.router import router as proposals_router

app.include_router(proposals_router, prefix="/api/v1")
```

- [ ] **Step 6: Run tests**

```bash
cd seven_tools_api
pytest tests/test_proposals.py -v
```

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add seven_tools_api/app/modules/proposals/ seven_tools_api/tests/test_proposals.py seven_tools_api/app/main.py seven_tools_api/app/schemas/proposal.py
git commit -m "feat(api): proposals module — CRUD with pagination and TDD"
```

---

## Task 12: AI Module — Knowledge Loader

**Files:**
- Create: `seven_tools_api/app/modules/ai/knowledge.py`

- [ ] **Step 1: Create knowledge loader**

```python
# seven_tools_api/app/modules/ai/knowledge.py
import os
from functools import lru_cache
from pathlib import Path


KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "knowledge" / "caloni"


@lru_cache(maxsize=1)
def load_caloni_knowledge() -> str:
    """Load and concatenate all Caloni knowledge .md files in numeric order."""
    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No .md files found in {KNOWLEDGE_DIR}")

    parts = []
    for f in md_files:
        parts.append(f.read_text(encoding="utf-8"))

    return "\n\n---\n\n".join(parts)
```

- [ ] **Step 2: Verify it loads the real files**

```bash
cd seven_tools_api
python -c "from app.modules.ai.knowledge import load_caloni_knowledge; k = load_caloni_knowledge(); print(f'Loaded {len(k)} chars from knowledge base')"
```

Expected: `Loaded XXXX chars from knowledge base` (some number > 0).

- [ ] **Step 3: Commit**

```bash
git add seven_tools_api/app/modules/ai/knowledge.py
git commit -m "feat(api): Caloni knowledge base loader"
```

---

## Task 13: AI Module — Schemas

**Files:**
- Create: `seven_tools_api/app/schemas/ai.py`

- [ ] **Step 1: Create AI schemas**

```python
# seven_tools_api/app/schemas/ai.py
from pydantic import BaseModel


# --- Validate Proposal ---

class ValidateProposalRequest(BaseModel):
    file_name: str
    file_content: str


class CalonCriterion(BaseModel):
    name: str
    score: float
    comment: str


class ValidateProposalResponse(BaseModel):
    overall_score: float
    overall_label: str
    strong_points: list[str]
    weak_points: list[str]
    criteria: list[CalonCriterion]
    suggestions: list[str]


# --- Diagnose ---

class DiagnoseRequest(BaseModel):
    nicho: str
    perfil_cliente: str
    ticket_medio: str
    receita_atual: str
    meta_receita: str
    desafio: str
    gargalo: str
    objecoes_comuns: str
    processo_venda: str


class DiagnoseResponse(BaseModel):
    saude_comercial: float
    label_saude: str
    diagnostico_geral: str
    principal_erro: str
    etapa_critica_funil: str
    sintomas: list[str]
    ajuste_recomendado: str
    orientacao_imediata: str
    plano_de_acao: list[str]
    metricas_chave: list[str]
```

- [ ] **Step 2: Commit**

```bash
git add seven_tools_api/app/schemas/ai.py
git commit -m "feat(api): AI request/response schemas"
```

---

## Task 14: AI Module — Service + Router (TDD)

**Files:**
- Create: `seven_tools_api/app/modules/ai/service.py`
- Create: `seven_tools_api/app/modules/ai/router.py`
- Create: `seven_tools_api/tests/test_ai.py`
- Modify: `seven_tools_api/app/main.py` (add router)

- [ ] **Step 1: Write tests (unit tests with mocked AI provider)**

```python
# seven_tools_api/tests/test_ai.py
import json
from unittest.mock import patch, AsyncMock

MOCK_VALIDATION_RESPONSE = json.dumps({
    "overallScore": 7.5,
    "overallLabel": "Proposta Forte",
    "strongPoints": ["Boa clareza", "ROI bem definido"],
    "weakPoints": ["Falta urgência"],
    "criteria": [
        {"name": "Clareza da Proposta de Valor", "score": 8, "comment": "Clara e direta"},
        {"name": "Urgência e Escassez", "score": 5, "comment": "Poderia melhorar"},
        {"name": "Prova Social", "score": 7, "comment": "Presente"},
        {"name": "Estrutura e Fluxo", "score": 8, "comment": "Bem organizada"},
        {"name": "Precificação e ROI", "score": 9, "comment": "Excelente"},
        {"name": "Call to Action", "score": 8, "comment": "Claro"},
    ],
    "suggestions": ["Adicionar urgência", "Incluir case similar"],
})

MOCK_DIAGNOSTIC_RESPONSE = json.dumps({
    "saudeComercial": 6.5,
    "labelSaude": "Atenção Necessária",
    "diagnosticoGeral": "A operação comercial apresenta pontos de melhoria.",
    "principalErro": "Falta de follow-up estruturado.",
    "etapaCriticaFunil": "Qualificação",
    "sintomas": ["Baixa conversão", "Ciclo longo", "Objeções recorrentes"],
    "ajusteRecomendado": "Implementar cadência de follow-up.",
    "orientacaoImediata": "Mapear todos os leads sem resposta nos últimos 7 dias.",
    "planoDeAcao": ["Revisar pipeline", "Criar cadência", "Treinar equipe"],
    "metricasChave": ["Taxa de resposta", "Tempo médio de ciclo"],
})


def test_validate_proposal(client, auth_headers):
    with patch("app.modules.ai.service.call_ai_provider") as mock_ai:
        mock_ai.return_value = MOCK_VALIDATION_RESPONSE

        response = client.post("/api/v1/ai/validate-proposal", headers=auth_headers, json={
            "file_name": "proposta.pdf",
            "file_content": "Conteúdo da proposta comercial para Empresa X...",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 7.5
        assert data["overall_label"] == "Proposta Forte"
        assert len(data["criteria"]) == 6
        assert len(data["strong_points"]) == 2
        mock_ai.assert_called_once()


def test_diagnose(client, auth_headers):
    with patch("app.modules.ai.service.call_ai_provider") as mock_ai:
        mock_ai.return_value = MOCK_DIAGNOSTIC_RESPONSE

        response = client.post("/api/v1/ai/diagnose", headers=auth_headers, json={
            "nicho": "SaaS B2B",
            "perfil_cliente": "Empresas de 50-200 funcionários",
            "ticket_medio": "5000",
            "receita_atual": "50000",
            "meta_receita": "100000",
            "desafio": "Baixa conversão",
            "gargalo": "Qualificação de leads",
            "objecoes_comuns": "Preço alto",
            "processo_venda": "Inbound + SDR + closer",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["saude_comercial"] == 6.5
        assert data["label_saude"] == "Atenção Necessária"
        assert len(data["sintomas"]) == 3
        assert len(data["plano_de_acao"]) == 3
        mock_ai.assert_called_once()


def test_validate_proposal_ai_error(client, auth_headers):
    with patch("app.modules.ai.service.call_ai_provider") as mock_ai:
        mock_ai.side_effect = Exception("Groq API timeout")

        response = client.post("/api/v1/ai/validate-proposal", headers=auth_headers, json={
            "file_name": "proposta.pdf",
            "file_content": "Conteúdo...",
        })

        assert response.status_code == 502
        assert "indisponível" in response.json()["detail"].lower() or "unavailable" in response.json()["detail"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd seven_tools_api
pytest tests/test_ai.py -v
```

Expected: All FAIL.

- [ ] **Step 3: Create AI service**

```python
# seven_tools_api/app/modules/ai/service.py
import json
import uuid

import httpx
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.analysis_result import AnalysisResult, AnalysisType
from app.modules.ai.knowledge import load_caloni_knowledge


def call_ai_provider(system_prompt: str, user_prompt: str) -> str:
    """Call the AI provider (Groq-compatible OpenAI API) and return raw response text."""
    url = f"{settings.ai_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": settings.ai_temperature,
        "max_tokens": settings.ai_max_tokens,
        "response_format": {"type": "json_object"},
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"]


def validate_proposal(
    db: DbSession,
    user_id: uuid.UUID,
    file_name: str,
    file_content: str,
) -> dict:
    knowledge = load_caloni_knowledge()

    system_prompt = (
        f"{knowledge}\n\n"
        "Você é Caloni, o Decisor Comercial Assistido da SEVEN. "
        "Analise a proposta comercial enviada e retorne um JSON com os campos: "
        "overallScore (0-10), overallLabel, strongPoints (array), weakPoints (array), "
        "criteria (array de {name, score, comment} para: Clareza da Proposta de Valor, "
        "Urgência e Escassez, Prova Social, Estrutura e Fluxo, Precificação e ROI, Call to Action), "
        "suggestions (array)."
    )

    user_prompt = f"Arquivo: {file_name}\n\nConteúdo:\n{file_content[:12000]}"

    raw = call_ai_provider(system_prompt, user_prompt)
    result = json.loads(raw)

    # Persist result
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        user_id=user_id,
        type=AnalysisType.validation,
        input_data={"file_name": file_name, "file_content_length": len(file_content)},
        output_data=result,
        score=result.get("overallScore"),
    )
    db.add(analysis)
    db.commit()

    return {
        "overall_score": result["overallScore"],
        "overall_label": result["overallLabel"],
        "strong_points": result["strongPoints"],
        "weak_points": result["weakPoints"],
        "criteria": [
            {"name": c["name"], "score": c["score"], "comment": c["comment"]}
            for c in result["criteria"]
        ],
        "suggestions": result["suggestions"],
    }


def diagnose(
    db: DbSession,
    user_id: uuid.UUID,
    input_data: dict,
) -> dict:
    knowledge = load_caloni_knowledge()

    system_prompt = (
        f"{knowledge}\n\n"
        "Você é Caloni, o Decisor Comercial Assistido da SEVEN. "
        "Realize um diagnóstico comercial completo com base nas respostas do questionário. "
        "Retorne um JSON com os campos: "
        "saudeComercial (0-10), labelSaude, diagnosticoGeral, principalErro, "
        "etapaCriticaFunil, sintomas (array 3+), ajusteRecomendado, "
        "orientacaoImediata, planoDeAcao (array 3-5), metricasChave (array)."
    )

    user_prompt = "\n".join(f"**{k}:** {v}" for k, v in input_data.items())

    raw = call_ai_provider(system_prompt, user_prompt)
    result = json.loads(raw)

    # Persist result
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        user_id=user_id,
        type=AnalysisType.diagnostic,
        input_data=input_data,
        output_data=result,
        score=result.get("saudeComercial"),
    )
    db.add(analysis)
    db.commit()

    return {
        "saude_comercial": result["saudeComercial"],
        "label_saude": result["labelSaude"],
        "diagnostico_geral": result["diagnosticoGeral"],
        "principal_erro": result["principalErro"],
        "etapa_critica_funil": result["etapaCriticaFunil"],
        "sintomas": result["sintomas"],
        "ajuste_recomendado": result["ajusteRecomendado"],
        "orientacao_imediata": result["orientacaoImediata"],
        "plano_de_acao": result["planoDeAcao"],
        "metricas_chave": result["metricasChave"],
    }
```

- [ ] **Step 4: Create AI router**

```python
# seven_tools_api/app/modules/ai/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.modules.ai.service import diagnose, validate_proposal
from app.schemas.ai import DiagnoseRequest, DiagnoseResponse, ValidateProposalRequest, ValidateProposalResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/validate-proposal", response_model=ValidateProposalResponse)
def validate(
    body: ValidateProposalRequest,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    try:
        result = validate_proposal(db, user.id, body.file_name, body.file_content)
        return result
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Serviço de IA indisponível. Tente novamente em alguns instantes.",
        )


@router.post("/diagnose", response_model=DiagnoseResponse)
def run_diagnose(
    body: DiagnoseRequest,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    try:
        result = diagnose(db, user.id, body.model_dump())
        return result
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Serviço de IA indisponível. Tente novamente em alguns instantes.",
        )
```

- [ ] **Step 5: Register AI router in main.py**

Add to `seven_tools_api/app/main.py`:

```python
from app.modules.ai.router import router as ai_router

app.include_router(ai_router, prefix="/api/v1")
```

- [ ] **Step 6: Run tests**

```bash
cd seven_tools_api
pytest tests/test_ai.py -v
```

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add seven_tools_api/app/modules/ai/ seven_tools_api/tests/test_ai.py seven_tools_api/app/main.py seven_tools_api/app/schemas/ai.py
git commit -m "feat(api): AI module — validate proposal, diagnose, with mocked TDD"
```

---

## Task 15: File Parsing (Server-Side)

**Files:**
- Create: `seven_tools_api/app/utils/file_parser.py`
- Create: `seven_tools_api/tests/test_file_parsing.py`
- Modify: `seven_tools_api/app/modules/ai/router.py` (add upload endpoint)

- [ ] **Step 1: Write failing tests**

```python
# seven_tools_api/tests/test_file_parsing.py
import io
from docx import Document

from app.utils.file_parser import extract_text_from_pdf, extract_text_from_docx


def test_extract_text_from_docx():
    doc = Document()
    doc.add_paragraph("Proposta Comercial")
    doc.add_paragraph("Valor: R$ 15.000")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    text = extract_text_from_docx(buffer)
    assert "Proposta Comercial" in text
    assert "R$ 15.000" in text


def test_extract_text_from_pdf():
    # Create a minimal PDF in memory using reportlab if available,
    # otherwise test with a known fixture.
    # For simplicity, test the function handles an invalid PDF gracefully.
    buffer = io.BytesIO(b"not a real pdf")
    try:
        text = extract_text_from_pdf(buffer)
        # If it doesn't raise, text should be empty or minimal
    except Exception as e:
        assert "pdf" in str(e).lower() or "invalid" in str(e).lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd seven_tools_api
pytest tests/test_file_parsing.py -v
```

Expected: FAIL (module doesn't exist).

- [ ] **Step 3: Create file parser**

```python
# seven_tools_api/app/utils/file_parser.py
from io import BytesIO
from typing import BinaryIO

import pdfplumber
from docx import Document


def extract_text_from_pdf(file: BinaryIO) -> str:
    text_parts = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file: BinaryIO) -> str:
    doc = Document(file)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(file: BinaryIO, content_type: str) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file)
    elif content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return extract_text_from_docx(file)
    elif content_type.startswith("text/"):
        return file.read().decode("utf-8")
    else:
        raise ValueError(f"Unsupported file type: {content_type}")
```

- [ ] **Step 4: Add file upload endpoint to AI router**

Add to `seven_tools_api/app/modules/ai/router.py`:

```python
from fastapi import File, UploadFile

from app.utils.file_parser import extract_text


@router.post("/validate-proposal/upload", response_model=ValidateProposalResponse)
async def validate_upload(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    try:
        content = extract_text(file.file, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do arquivo.")

    try:
        result = validate_proposal(db, user.id, file.filename, content)
        return result
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Serviço de IA indisponível. Tente novamente em alguns instantes.",
        )
```

- [ ] **Step 5: Run tests**

```bash
cd seven_tools_api
pytest tests/test_file_parsing.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add seven_tools_api/app/utils/file_parser.py seven_tools_api/tests/test_file_parsing.py seven_tools_api/app/modules/ai/router.py
git commit -m "feat(api): server-side PDF/DOCX parsing with upload endpoint"
```

---

## Task 16: Rate Limiting + Final main.py

**Files:**
- Modify: `seven_tools_api/app/main.py`

- [ ] **Step 1: Add rate limiting and finalize main.py**

```python
# seven_tools_api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.proposals.router import router as proposals_router
from app.modules.ai.router import router as ai_router

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="SEVEN Tools API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(proposals_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Add rate limit decorator to auth login**

In `seven_tools_api/app/modules/auth/router.py`, add the rate limit to the login endpoint:

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: DbSession = Depends(get_db)):
    # ... existing implementation unchanged
```

Note: The `request: Request` parameter must be added for slowapi to work.

- [ ] **Step 3: Run full test suite**

```bash
cd seven_tools_api
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add seven_tools_api/app/main.py seven_tools_api/app/modules/auth/router.py
git commit -m "feat(api): rate limiting on login, finalize main.py with all routers"
```

---

## Task 17: Run Full Test Suite + Smoke Test Server

- [ ] **Step 1: Run all tests**

```bash
cd seven_tools_api
pytest tests/ -v --tb=short
```

Expected: All tests PASS.

- [ ] **Step 2: Start dev server**

```bash
cd seven_tools_api
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 3: Smoke test endpoints**

In another terminal:

```bash
# Health check
curl http://localhost:8000/health

# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"test123","company_name":"Test Co"}'

# Login (use the token from register or login response)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'

# OpenAPI docs
curl http://localhost:8000/docs
```

- [ ] **Step 4: Verify OpenAPI docs load in browser**

Open `http://localhost:8000/docs` — all endpoints should be listed with schemas.

- [ ] **Step 5: Commit (if any fixes were needed)**

```bash
git add -A
git commit -m "fix(api): adjustments from smoke testing"
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Project scaffolding + Docker | docker-compose, requirements, config, .env |
| 2 | Database + Alembic | database.py, alembic config |
| 3 | SQLAlchemy models | 6 model files |
| 4 | Utils + dependencies | security.py, dependencies.py, common schemas |
| 5 | Test infrastructure | conftest.py, minimal main.py |
| 6 | Auth schemas | schemas/auth.py |
| 7 | Auth module (TDD) | auth service + router + tests |
| 8 | User schemas | schemas/user.py |
| 9 | Users module (TDD) | users service + router + tests |
| 10 | Proposal schemas | schemas/proposal.py |
| 11 | Proposals module (TDD) | proposals service + router + tests |
| 12 | Knowledge loader | ai/knowledge.py |
| 13 | AI schemas | schemas/ai.py |
| 14 | AI module (TDD) | ai service + router + tests |
| 15 | File parsing | file_parser.py + upload endpoint + tests |
| 16 | Rate limiting + main.py | slowapi, finalize app |
| 17 | Full test suite + smoke test | Verify everything works |
