import uuid
from datetime import datetime, timedelta, timezone

from app.models.company import Company
from app.models.company_request import CompanyRequest, CompanyRequestStatus
from app.models.session import Session
from app.models.user import ApprovalSource, Role, User, ValidationStatus
from app.utils.security import generate_token, hash_password


def _create_authenticated_user(
    db,
    *,
    email: str,
    role: Role = Role.user,
    validation_status: ValidationStatus = ValidationStatus.approved,
    company_id=None,
):
    user = User(
        id=uuid.uuid4(),
        company_id=company_id,
        name=email.split("@")[0],
        email=email,
        password_hash=hash_password("password123"),
        role=role,
        validation_status=validation_status,
        approval_source=ApprovalSource.seed if validation_status == ValidationStatus.approved else None,
    )
    db.add(user)
    db.flush()

    token = generate_token()
    db.add(
        Session(
            id=uuid.uuid4(),
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db.commit()
    db.refresh(user)
    return user, {"Authorization": f"Bearer {token}"}


def test_admin_lists_pending_reviews_with_selected_company_context(client, db, sample_company):
    sample_company.source = "clickup"
    sample_company.contact_email = "responsavel@example.com"
    sample_company.partner_1_name = "Socio A"
    sample_company.partner_2_name = "Socio B"
    sample_company.has_contract = True
    sample_company.clickup_status = "sevem"
    sample_company.clickup_tags = ["cliente ativo"]
    db.commit()

    _, admin_headers = _create_authenticated_user(
        db,
        email="admin@example.com",
        role=Role.admin,
        company_id=sample_company.id,
    )
    pending_user, _ = _create_authenticated_user(
        db,
        email="pending@example.com",
        validation_status=ValidationStatus.pending_review,
        company_id=sample_company.id,
    )

    response = client.get("/api/v1/membership/reviews", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["user"]["id"] == str(pending_user.id)
    assert item["user"]["name"] == pending_user.name
    assert item["user"]["email"] == "pending@example.com"
    assert item["user"]["validation_status"] == "pending_review"
    assert item["user"]["company_id"] == str(sample_company.id)
    assert item["selected_company_name"] == "Test Company"
    assert item["contact_email"] == "responsavel@example.com"
    assert item["partner_1_name"] == "Socio A"
    assert item["partner_2_name"] == "Socio B"
    assert item["has_contract"] is True
    assert item["requested_company_name"] is None
    assert item["requested_cnpj"] is None


def test_admin_lists_pending_reviews_with_other_company_request_context(client, db):
    _, admin_headers = _create_authenticated_user(
        db,
        email="admin@example.com",
        role=Role.admin,
    )
    pending_user, _ = _create_authenticated_user(
        db,
        email="pending@example.com",
        validation_status=ValidationStatus.pending_review,
    )

    db.add(
        CompanyRequest(
            requested_by_user_id=pending_user.id,
            requested_company_name="Other Company",
            requested_cnpj="12.345.678/0001-90",
        )
    )
    db.commit()

    response = client.get("/api/v1/membership/reviews", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["user"]["id"] == str(pending_user.id)
    assert item["user"]["name"] == pending_user.name
    assert item["user"]["email"] == "pending@example.com"
    assert item["user"]["validation_status"] == "pending_review"
    assert item["user"]["company_id"] is None
    assert item["selected_company_name"] is None
    assert item["contact_email"] is None
    assert item["partner_1_name"] is None
    assert item["partner_2_name"] is None
    assert item["has_contract"] is False
    assert item["requested_company_name"] == "Other Company"
    assert item["requested_cnpj"] == "12.345.678/0001-90"


def test_admin_approves_pending_user_and_fills_metadata(client, db):
    admin_user, admin_headers = _create_authenticated_user(
        db,
        email="admin@example.com",
        role=Role.admin,
    )
    pending_user, _ = _create_authenticated_user(
        db,
        email="pending-other@example.com",
        validation_status=ValidationStatus.pending_review,
    )
    db.add(
        CompanyRequest(
            requested_by_user_id=pending_user.id,
            requested_company_name="Created Company",
            requested_cnpj="12.345.678/0001-90",
        )
    )
    db.commit()

    response = client.post(
        f"/api/v1/membership/reviews/{pending_user.id}/approve",
        headers=admin_headers,
        json={"create_company_from_request": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(pending_user.id)
    assert data["user"]["validation_status"] == "approved"
    assert data["user"]["approval_source"] == "manual"
    assert data["company"]["name"] == "Created Company"
    assert data["company"]["cnpj"] == "12.345.678/0001-90"

    db.refresh(pending_user)
    assert pending_user.validation_status == ValidationStatus.approved
    assert pending_user.approval_source == ApprovalSource.manual
    assert pending_user.approved_at is not None
    assert pending_user.approved_by_user_id == admin_user.id
    assert pending_user.company is not None
    assert pending_user.company.name == "Created Company"
    assert pending_user.company.cnpj == "12.345.678/0001-90"

    company_request = db.query(CompanyRequest).filter(CompanyRequest.requested_by_user_id == pending_user.id).one()
    assert company_request.status == CompanyRequestStatus.resolved


def test_admin_cannot_approve_other_request_without_resolving_company(client, db):
    _, admin_headers = _create_authenticated_user(
        db,
        email="admin@example.com",
        role=Role.admin,
    )
    pending_user, _ = _create_authenticated_user(
        db,
        email="pending-other@example.com",
        validation_status=ValidationStatus.pending_review,
    )
    db.add(
        CompanyRequest(
            requested_by_user_id=pending_user.id,
            requested_company_name="Created Company",
            requested_cnpj="12.345.678/0001-90",
        )
    )
    db.commit()

    response = client.post(
        f"/api/v1/membership/reviews/{pending_user.id}/approve",
        headers=admin_headers,
        json={},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "COMPANY_RESOLUTION_REQUIRED"

    db.refresh(pending_user)
    assert pending_user.validation_status == ValidationStatus.pending_review
    assert pending_user.approval_source is None
    assert pending_user.company_id is None

    company_request = db.query(CompanyRequest).filter(CompanyRequest.requested_by_user_id == pending_user.id).one()
    assert company_request.status == CompanyRequestStatus.pending


def test_admin_blocks_pending_user(client, db):
    admin_user, admin_headers = _create_authenticated_user(
        db,
        email="admin@example.com",
        role=Role.admin,
    )
    pending_user, _ = _create_authenticated_user(
        db,
        email="blocked@example.com",
        validation_status=ValidationStatus.pending_review,
    )

    response = client.post(
        f"/api/v1/membership/reviews/{pending_user.id}/block",
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(pending_user.id)
    assert data["user"]["validation_status"] == "blocked"
    assert data["user"]["approval_source"] == "manual"

    db.refresh(pending_user)
    assert pending_user.validation_status == ValidationStatus.blocked
    assert pending_user.approval_source == ApprovalSource.manual
    assert pending_user.approved_at is not None
    assert pending_user.approved_by_user_id == admin_user.id


def test_pending_review_user_loses_access_to_protected_product_endpoint(client, db, sample_company):
    _, pending_headers = _create_authenticated_user(
        db,
        email="pending@example.com",
        validation_status=ValidationStatus.pending_review,
        company_id=sample_company.id,
    )

    response = client.get("/api/v1/proposals", headers=pending_headers)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "VALIDATION_PENDING"


def test_get_me_still_accessible_for_pending_review_user(client, db, sample_company):
    pending_user, pending_headers = _create_authenticated_user(
        db,
        email="pending-me@example.com",
        validation_status=ValidationStatus.pending_review,
        company_id=sample_company.id,
    )

    response = client.get("/api/v1/users/me", headers=pending_headers)

    assert response.status_code == 200
    assert response.json()["id"] == str(pending_user.id)
    assert response.json()["validation_status"] == "pending_review"
