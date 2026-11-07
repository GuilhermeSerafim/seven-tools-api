# seven_tools_api/tests/conftest.py
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import Base
from app.dependencies import get_db
from app.main import app, limiter
from app.modules.auth.router import limiter as auth_limiter
from app.models.company import Company
from app.models.company_request import CompanyRequest
from app.models.session import Session
from app.models.user import ApprovalSource, User, ValidationStatus
from app.utils.security import generate_token, hash_password
from tests.support import SEEDED_SECRET


TEST_SCHEMA = "seven_tools_api_test"

admin_engine = create_engine(settings.database_url_test, poolclass=NullPool)


@pytest.fixture
def test_schema_name():
    return f"{TEST_SCHEMA}_{uuid.uuid4().hex}"


@pytest.fixture
def test_engine(test_schema_name):
    engine = create_engine(
        settings.database_url_test,
        connect_args={"options": f"-csearch_path={test_schema_name}"},
        poolclass=NullPool,
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def setup_db(request, test_schema_name, test_engine):
    if request.node.get_closest_marker("migration_smoke"):
        yield
        return

    with admin_engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {test_schema_name} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {test_schema_name}"))
    Base.metadata.create_all(bind=test_engine)
    yield
    with admin_engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {test_schema_name} CASCADE"))


@pytest.fixture
def db(test_engine):
    session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    auth_limiter.reset()
    yield


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
        password_hash=hash_password(SEEDED_SECRET),
        role="user",
        validation_status=ValidationStatus.approved,
        approval_source=ApprovalSource.seed,
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
