import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DbSession, selectinload

from app.models.company import Company
from app.models.company_request import CompanyRequestStatus
from app.models.user import ApprovalSource, User, ValidationStatus


def list_pending_reviews(db: DbSession) -> list[dict]:
    users = (
        db.query(User)
        .options(selectinload(User.company), selectinload(User.company_request))
        .filter(User.validation_status == ValidationStatus.pending_review)
        .order_by(User.created_at.asc())
        .all()
    )

    items = []
    for user in users:
        items.append(
            {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "validation_status": user.validation_status.value,
                    "company_id": user.company_id,
                },
                "selected_company_name": user.company.name if user.company is not None else None,
                "contact_email": user.company.contact_email if user.company is not None else None,
                "partner_1_name": user.company.partner_1_name if user.company is not None else None,
                "partner_2_name": user.company.partner_2_name if user.company is not None else None,
                "has_contract": user.company.has_contract if user.company is not None else False,
                "requested_company_name": (
                    user.company_request.requested_company_name if user.company_request is not None else None
                ),
                "requested_cnpj": user.company_request.requested_cnpj if user.company_request is not None else None,
            }
        )
    return items


def approve_review(
    db: DbSession,
    user_id: uuid.UUID,
    admin_user_id: uuid.UUID,
    company_id: uuid.UUID | None = None,
    create_company_from_request: bool = False,
) -> dict:
    user = _get_pending_user(db, user_id)
    _require_company_resolution(user, company_id, create_company_from_request)
    company = user.company

    if company_id is not None:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Empresa não encontrada.", "code": "COMPANY_NOT_FOUND"},
            )
    elif create_company_from_request:
        if user.company_request is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"detail": "Solicitação de empresa não encontrada.", "code": "COMPANY_REQUEST_NOT_FOUND"},
            )
        company = _get_or_create_company_from_request(db, user)

    if company is not None:
        user.company_id = company.id

    user.validation_status = ValidationStatus.approved
    user.approval_source = ApprovalSource.manual
    user.approved_at = datetime.now(timezone.utc)
    user.approved_by_user_id = admin_user_id

    if user.company_request is not None:
        user.company_request.status = CompanyRequestStatus.resolved

    db.commit()
    db.refresh(user)
    if company is not None:
        db.refresh(company)
    return _action_response(user, company)


def block_review(db: DbSession, user_id: uuid.UUID, admin_user_id: uuid.UUID) -> dict:
    user = _get_pending_user(db, user_id)

    user.validation_status = ValidationStatus.blocked
    user.approval_source = ApprovalSource.manual
    user.approved_at = datetime.now(timezone.utc)
    user.approved_by_user_id = admin_user_id

    if user.company_request is not None:
        user.company_request.status = CompanyRequestStatus.rejected

    db.commit()
    db.refresh(user)
    return _action_response(user, user.company)


def _get_pending_user(db: DbSession, user_id: uuid.UUID) -> User:
    user = (
        db.query(User)
        .options(selectinload(User.company), selectinload(User.company_request))
        .filter(User.id == user_id)
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Usuário não encontrado.", "code": "USER_NOT_FOUND"},
        )
    if user.validation_status != ValidationStatus.pending_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Usuário não está com revisão pendente.", "code": "USER_NOT_PENDING_REVIEW"},
        )
    return user


def _get_or_create_company_from_request(db: DbSession, user: User) -> Company:
    request = user.company_request
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Solicitação de empresa não encontrada.", "code": "COMPANY_REQUEST_NOT_FOUND"},
        )

    company = None
    if request.requested_cnpj is not None:
        company = db.query(Company).filter(Company.cnpj == request.requested_cnpj).first()

    if company is None:
        company = Company(
            id=uuid.uuid4(),
            name=request.requested_company_name,
            cnpj=request.requested_cnpj,
        )
        db.add(company)
        db.flush()

    return company


def _action_response(user: User, company: Company | None) -> dict:
    return {
        "user": {
            "id": user.id,
            "validation_status": user.validation_status.value,
            "approval_source": user.approval_source.value if user.approval_source is not None else None,
            "approved_at": user.approved_at,
            "approved_by_user_id": user.approved_by_user_id,
            "company_id": user.company_id,
        },
        "company": (
            {
                "id": company.id,
                "name": company.name,
                "cnpj": company.cnpj,
            }
            if company is not None
            else None
        ),
    }


def _require_company_resolution(
    user: User,
    company_id: uuid.UUID | None,
    create_company_from_request: bool,
) -> None:
    if user.company_request is None:
        return
    if company_id is not None or create_company_from_request:
        return
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"detail": "Resolva a empresa antes de aprovar a revisão.", "code": "COMPANY_RESOLUTION_REQUIRED"},
    )
