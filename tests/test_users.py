# seven_tools_api/tests/test_users.py
import uuid

from app.models.company import Company
from app.models.company_request import CompanyRequest, CompanyRequestStatus
from app.models.user import User, ValidationStatus
from app.modules.auth.router import limiter as auth_limiter
from app.utils.security import hash_password
from tests.support import ALT_SECRET, FIXTURE_HASH, SEEDED_SECRET, TEST_SECRET, with_secret, with_secret_hash


def test_get_me(client, auth_headers, sample_user, sample_company):
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["validation_status"] == "approved"
    assert data["approval_source"] == "seed"
    assert data["company"]["name"] == "Test Company"
    assert set(data["company"].keys()) == {
        "id",
        "name",
        "logo_url",
        "website",
        "instagram",
        "segment",
        "short_description",
        "city",
    }


def test_membership_validation_model_contract(db, sample_user):
    company = Company(name="Contract Company")
    db.add(company)
    db.commit()
    db.refresh(company)

    assert company.source == "manual"
    assert company.has_contract is False

    request = CompanyRequest(
        requested_by_user_id=sample_user.id,
        requested_company_name="Other Company",
        requested_cnpj="12.345.678/0001-90",
        status=CompanyRequestStatus.resolved,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    db.refresh(sample_user)

    assert request.requested_by_user_id == sample_user.id
    assert request.requested_company_name == "Other Company"
    assert request.requested_cnpj == "12.345.678/0001-90"
    assert request.status == CompanyRequestStatus.resolved
    assert request.created_at is not None
    assert sample_user.company_request is not None
    assert sample_user.company_request.id == request.id
    assert not hasattr(request, "updated_at")


def test_new_user_defaults_and_clickup_tags_mutation(db, sample_company):
    new_user = User(**with_secret_hash({
        "company_id": sample_company.id,
        "name": "Pending User",
        "email": "pending@example.com",
        "role": "user",
    }, FIXTURE_HASH))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    assert new_user.validation_status == ValidationStatus.pending_review
    assert new_user.approval_source is None

    company = Company(name="Mutable Tags Co", clickup_tags=["priority"])
    db.add(company)
    db.commit()

    company.clickup_tags.append("vip")
    db.commit()
    db.refresh(company)

    assert company.clickup_tags == ["priority", "vip"]


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


def test_update_me_normalizes_email_and_preserves_login_and_duplicate_checks(client, auth_headers, db, sample_user, sample_company):
    response = client.put("/api/v1/users/me", headers=auth_headers, json={
        "email": "  UPDATED@EXAMPLE.COM ",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"

    db.refresh(sample_user)
    assert sample_user.email == "updated@example.com"

    auth_limiter._storage.reset()
    login_response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "  UpDaTeD@Example.Com ",
    }, SEEDED_SECRET))
    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == "updated@example.com"

    duplicate_response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "Another User",
        "email": "  UPDATED@EXAMPLE.COM ",
        "company_id": str(sample_company.id),
    }, ALT_SECRET))
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"]["code"] == "EMAIL_EXISTS"


def test_update_me_returns_conflict_for_case_insensitive_email_collision(client, auth_headers, db, sample_company):
    other_user = User(**with_secret_hash({
        "id": uuid.uuid4(),
        "company_id": sample_company.id,
        "name": "Other User",
        "email": "OtherUser@Example.com",
        "role": "user",
    }, hash_password(TEST_SECRET)))
    db.add(other_user)
    db.commit()

    response = client.put("/api/v1/users/me", headers=auth_headers, json={
        "email": "  otheruser@example.com ",
    })

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EMAIL_EXISTS"


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
