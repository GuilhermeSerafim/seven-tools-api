# seven_tools_api/app/modules/auth/service.py
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.company import Company
from app.models.company_request import CompanyRequest
from app.models.session import Session
from app.models.user import ApprovalSource, User, ValidationStatus
from app.utils.security import generate_token, hash_password, verify_password


def register_user(
    db: DbSession,
    name: str,
    email: str,
    password: str,
    company_id: uuid.UUID | None = None,
    other_company_name: str | None = None,
    other_company_cnpj: str | None = None,
) -> tuple[User | None, str]:
    normalized_email = email.strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if existing:
        return None, "EMAIL_EXISTS"

    company = None
    validation_status = ValidationStatus.pending_review
    approval_source = None
    approved_at = None

    if company_id is not None:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company is None:
            return None, "COMPANY_NOT_FOUND"

        normalized_company_contact_email = (
            company.contact_email.strip().lower()
            if company.contact_email is not None
            else None
        )
        if normalized_company_contact_email == normalized_email:
            validation_status = ValidationStatus.approved
            approval_source = ApprovalSource.clickup_email_match
            approved_at = datetime.now(timezone.utc)

    user = User(
        id=uuid.uuid4(),
        company_id=company.id if company is not None else None,
        name=name,
        email=normalized_email,
        password_hash=hash_password(password),
        validation_status=validation_status,
        approval_source=approval_source,
        approved_at=approved_at,
    )
    db.add(user)
    db.flush()

    if company is None:
        db.add(
            CompanyRequest(
                requested_by_user_id=user.id,
                requested_company_name=other_company_name,
                requested_cnpj=other_company_cnpj,
            )
        )

    token = _create_session(db, user.id)
    db.commit()
    db.refresh(user)
    return user, token


def authenticate(db: DbSession, email: str, password: str) -> tuple[User | None, str | None]:
    normalized_email = email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
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


def change_password(db: DbSession, user: User, current_password: str, new_password: str) -> bool:
    if not verify_password(current_password, user.password_hash):
        return False
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
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
