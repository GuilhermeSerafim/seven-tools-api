import uuid

from app.models.company import Company
from app.models.company_request import CompanyRequest, CompanyRequestStatus
from app.models.user import ApprovalSource, User, ValidationStatus
from app.utils.security import hash_password
from tests.support import FIXTURE_HASH, NEW_SECRET, SEEDED_SECRET, TEST_SECRET, UNKNOWN_SECRET, WRONG_SECRET, change_secret_payload, with_secret, with_secret_hash


def test_register_auto_approves_when_selected_company_email_matches_exactly(client, db):
    company = Company(
        id=uuid.uuid4(),
        name="Match Company",
        contact_email="  OWNER@MATCH.CO ",
    )
    db.add(company)
    db.commit()

    response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "New User",
        "email": "  OWNER@MATCH.CO ",
        "company_id": str(company.id),
    }, TEST_SECRET))

    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert data["user"]["name"] == "New User"
    assert data["user"]["email"] == "owner@match.co"
    assert data["user"]["role"] == "user"
    assert data["user"]["validation_status"] == "approved"
    assert data["user"]["approval_source"] == "clickup_email_match"
    assert data["user"]["company_id"] == str(company.id)

    created_user = db.query(User).filter(User.email == "owner@match.co").one()
    assert created_user.company_id == company.id
    assert created_user.validation_status == ValidationStatus.approved
    assert created_user.approval_source == ApprovalSource.clickup_email_match
    assert created_user.approved_at is not None
    assert db.query(CompanyRequest).count() == 0


def test_register_selected_company_without_email_match_stays_pending_review(client, db):
    company = Company(
        id=uuid.uuid4(),
        name="Pending Company",
        contact_email="owner@pending.co",
    )
    db.add(company)
    db.commit()

    response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "Pending User",
        "email": "member@pending.co",
        "company_id": str(company.id),
    }, TEST_SECRET))

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["validation_status"] == "pending_review"
    assert data["user"]["approval_source"] is None
    assert data["user"]["company_id"] == str(company.id)

    created_user = db.query(User).filter(User.email == "member@pending.co").one()
    assert created_user.company_id == company.id
    assert created_user.validation_status == ValidationStatus.pending_review
    assert created_user.approval_source is None
    assert created_user.approved_at is None
    assert db.query(CompanyRequest).count() == 0


def test_register_other_company_creates_pending_review_and_company_request(client, db):
    response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "Other User",
        "email": "other@example.com",
        "other_company_name": "Other Company",
        "other_company_cnpj": "12.345.678/0001-90",
    }, TEST_SECRET))

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["validation_status"] == "pending_review"
    assert data["user"]["approval_source"] is None
    assert data["user"]["company_id"] is None

    created_user = db.query(User).filter(User.email == "other@example.com").one()
    assert created_user.company_id is None
    assert created_user.validation_status == ValidationStatus.pending_review
    assert created_user.approval_source is None
    assert created_user.approved_at is None

    company_request = db.query(CompanyRequest).filter(CompanyRequest.requested_by_user_id == created_user.id).one()
    assert company_request.requested_company_name == "Other Company"
    assert company_request.requested_cnpj == "12.345.678/0001-90"
    assert company_request.status == CompanyRequestStatus.pending


def test_register_duplicate_email_conflicts_with_normalized_email(client, sample_company, sample_user):
    response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "Another User",
        "email": "  TEST@EXAMPLE.COM ",
        "company_id": str(sample_company.id),
    }, TEST_SECRET))
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EMAIL_EXISTS"


def test_register_duplicate_email_conflicts_with_legacy_mixed_case_email(client, db, sample_company):
    legacy_user = User(**with_secret_hash({
        "id": uuid.uuid4(),
        "company_id": sample_company.id,
        "name": "Legacy User",
        "email": "Legacy@Example.com",
        "role": "user",
    }, FIXTURE_HASH))
    db.add(legacy_user)
    db.commit()

    response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "Another User",
        "email": "  legacy@example.com ",
        "company_id": str(sample_company.id),
    }, TEST_SECRET))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EMAIL_EXISTS"


def test_register_returns_error_when_company_id_does_not_exist(client):
    response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "New User",
        "email": "new@example.com",
        "company_id": str(uuid.uuid4()),
    }, TEST_SECRET))
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "COMPANY_NOT_FOUND"


def test_login_success(client, sample_user):
    response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "test@example.com",
    }, SEEDED_SECRET))
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"


def test_login_normalizes_email_with_whitespace_and_casing(client, db):
    company = Company(
        id=uuid.uuid4(),
        name="Login Match Company",
        contact_email="login@example.com",
    )
    db.add(company)
    db.commit()

    register_response = client.post("/api/v1/auth/register", json=with_secret({
        "name": "Login User",
        "email": "  LOGIN@EXAMPLE.COM ",
        "company_id": str(company.id),
    }, TEST_SECRET))
    assert register_response.status_code == 201

    response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "  LoGiN@Example.Com ",
    }, TEST_SECRET))

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "login@example.com"


def test_login_accepts_legacy_mixed_case_email_with_any_casing(client, db, sample_company):
    legacy_user = User(**with_secret_hash({
        "id": uuid.uuid4(),
        "company_id": sample_company.id,
        "name": "Legacy Login User",
        "email": "Legacy@Example.com",
        "role": "user",
    }, hash_password(TEST_SECRET)))
    db.add(legacy_user)
    db.commit()

    response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "  LEGACY@example.com ",
    }, TEST_SECRET))

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "Legacy@Example.com"


def test_login_wrong_password(client, sample_user):
    response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "test@example.com",
    }, WRONG_SECRET))
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_email(client):
    response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "nobody@example.com",
    }, UNKNOWN_SECRET))
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_logout_success(client, auth_headers):
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200

    # Token should no longer work
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 401


def test_login_response_includes_must_change_password(client, sample_user):
    response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "test@example.com",
    }, SEEDED_SECRET))
    assert response.status_code == 200
    data = response.json()
    assert "must_change_password" in data["user"]
    assert data["user"]["must_change_password"] is False


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


def test_change_password_success(client, db, sample_user, auth_headers):
    sample_user.must_change_password = True
    db.commit()

    response = client.post("/api/v1/auth/change-password", headers=auth_headers,
                           json=change_secret_payload(SEEDED_SECRET, NEW_SECRET))
    assert response.status_code == 200
    assert response.json()["detail"] == "Senha alterada com sucesso."

    db.refresh(sample_user)
    assert sample_user.must_change_password is False

    # Verify new password works
    login_response = client.post("/api/v1/auth/login", json=with_secret({
        "email": "test@example.com",
    }, NEW_SECRET))
    assert login_response.status_code == 200


def test_change_password_wrong_current(client, db, sample_user, auth_headers):
    response = client.post("/api/v1/auth/change-password", headers=auth_headers,
                           json=change_secret_payload(WRONG_SECRET, NEW_SECRET))
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_CURRENT_PASSWORD"


def test_change_password_same_as_current(client, db, sample_user, auth_headers):
    response = client.post("/api/v1/auth/change-password", headers=auth_headers,
                           json=change_secret_payload(SEEDED_SECRET, SEEDED_SECRET))
    assert response.status_code == 422


def test_change_password_too_short(client, db, sample_user, auth_headers):
    response = client.post("/api/v1/auth/change-password", headers=auth_headers,
                           json=change_secret_payload(SEEDED_SECRET, "ab"))
    assert response.status_code == 422


def test_change_password_requires_auth(client):
    response = client.post("/api/v1/auth/change-password",
                           json=change_secret_payload("whatever", NEW_SECRET))
    assert response.status_code == 422
