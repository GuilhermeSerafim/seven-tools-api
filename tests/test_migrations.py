import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.config import settings
from tests.support import FIXTURE_HASH, with_secret_hash


@pytest.mark.migration_smoke
def test_migration_chain_upgrades_clean_db_and_backfills_existing_users():
    base_url = make_url(settings.database_url_test)
    admin_url = base_url.set(database="postgres")
    temp_db_name = f"seven_tools_migration_smoke_{uuid.uuid4().hex[:8]}"
    temp_db_url = base_url.set(database=temp_db_name).render_as_string(hide_password=False)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    temp_engine = None
    original_database_url = settings.database_url

    try:
        with admin_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {temp_db_name}"))

        settings.database_url = temp_db_url
        alembic_cfg = Config("alembic.ini")

        command.upgrade(alembic_cfg, "5f1c9d7a2a10")

        temp_engine = create_engine(temp_db_url)
        company_id = uuid.uuid4()
        user_id = uuid.uuid4()

        with temp_engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO companies (id, name, created_at, updated_at)
                    VALUES (:id, :name, NOW(), NOW())
                    """
                ),
                {"id": company_id, "name": "Legacy Company"},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO users (id, company_id, name, email, password_hash, role, created_at, updated_at)
                    VALUES (:id, :company_id, :name, :email, :password_hash, :role, NOW(), NOW())
                    """
                ),
                with_secret_hash(
                    {
                        "id": user_id,
                        "company_id": company_id,
                        "name": "Legacy User",
                        "email": "legacy@example.com",
                        "role": "user",
                    },
                    FIXTURE_HASH,
                ),
            )

        command.upgrade(alembic_cfg, "head")

        with temp_engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT validation_status, approval_source
                    FROM users
                    WHERE id = :id
                    """
                ),
                {"id": user_id},
            ).one()

        assert row.validation_status == "approved"
        assert row.approval_source == "seed"
    finally:
        settings.database_url = original_database_url
        if temp_engine is not None:
            temp_engine.dispose()
        admin_engine.dispose()
        cleanup_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        try:
            with cleanup_engine.connect() as conn:
                conn.execute(text(f"DROP DATABASE IF EXISTS {temp_db_name}"))
        finally:
            cleanup_engine.dispose()


@pytest.mark.migration_smoke
def test_head_migration_enforces_case_insensitive_unique_users_email():
    base_url = make_url(settings.database_url_test)
    admin_url = base_url.set(database="postgres")
    temp_db_name = f"seven_tools_migration_email_index_{uuid.uuid4().hex[:8]}"
    temp_db_url = base_url.set(database=temp_db_name).render_as_string(hide_password=False)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    temp_engine = None
    original_database_url = settings.database_url

    try:
        with admin_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {temp_db_name}"))

        settings.database_url = temp_db_url
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        temp_engine = create_engine(temp_db_url)
        company_id = uuid.uuid4()

        with temp_engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO companies (id, name, created_at, updated_at)
                    VALUES (:id, :name, NOW(), NOW())
                    """
                ),
                {"id": company_id, "name": "Email Index Company"},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO users (id, company_id, name, email, password_hash, role, validation_status, created_at, updated_at)
                    VALUES (:id, :company_id, :name, :email, :password_hash, :role, :validation_status, NOW(), NOW())
                    """
                ),
                with_secret_hash(
                    {
                        "id": uuid.uuid4(),
                        "company_id": company_id,
                        "name": "Legacy User",
                        "email": "Legacy@Example.com",
                        "role": "user",
                        "validation_status": "approved",
                    },
                    FIXTURE_HASH,
                ),
            )

        with temp_engine.connect() as conn:
            indexes = conn.execute(
                text(
                    """
                    SELECT indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND tablename = 'users'
                      AND indexname = 'uq_users_email_lower'
                    """
                )
            ).fetchall()

        assert len(indexes) == 1
        assert "lower" in indexes[0].indexdef.lower()
        assert "email" in indexes[0].indexdef.lower()

        with pytest.raises(IntegrityError):
            with temp_engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO users (id, company_id, name, email, password_hash, role, validation_status, created_at, updated_at)
                        VALUES (:id, :company_id, :name, :email, :password_hash, :role, :validation_status, NOW(), NOW())
                        """
                    ),
                    with_secret_hash(
                        {
                            "id": uuid.uuid4(),
                            "company_id": company_id,
                            "name": "Duplicate User",
                            "email": "legacy@example.com",
                            "role": "user",
                            "validation_status": "approved",
                        },
                        FIXTURE_HASH,
                    ),
                )
    finally:
        settings.database_url = original_database_url
        if temp_engine is not None:
            temp_engine.dispose()
        admin_engine.dispose()
        cleanup_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        try:
            with cleanup_engine.connect() as conn:
                conn.execute(text(f"DROP DATABASE IF EXISTS {temp_db_name}"))
        finally:
            cleanup_engine.dispose()
