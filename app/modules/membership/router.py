import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_admin, get_db
from app.models.user import User
from app.modules.clickup.service import ClickupConfigurationError, ClickupFetchError
from app.modules.companies.service import sync_clickup_directory
from app.modules.membership.service import approve_review, block_review, list_pending_reviews
from app.schemas.membership import (
    MembershipApproveRequest,
    MembershipClickupSyncResponse,
    MembershipReviewActionResponse,
    MembershipReviewListResponse,
)

router = APIRouter(prefix="/membership", tags=["membership"])

AdminUserDep = Annotated[User, Depends(get_current_admin)]
DbSessionDep = Annotated[DbSession, Depends(get_db)]


@router.get("/reviews", response_model=MembershipReviewListResponse)
def get_reviews(
    admin_user: AdminUserDep,
    db: DbSessionDep,
):
    del admin_user
    return MembershipReviewListResponse(items=list_pending_reviews(db))


@router.post("/reviews/{user_id}/approve", response_model=MembershipReviewActionResponse)
def approve_user_review(
    user_id: uuid.UUID,
    admin_user: AdminUserDep,
    db: DbSessionDep,
    body: MembershipApproveRequest | None = None,
):
    body = body or MembershipApproveRequest()
    return approve_review(
        db,
        user_id=user_id,
        admin_user_id=admin_user.id,
        company_id=body.company_id,
        create_company_from_request=body.create_company_from_request,
    )


@router.post("/reviews/{user_id}/block", response_model=MembershipReviewActionResponse)
def block_user_review(
    user_id: uuid.UUID,
    admin_user: AdminUserDep,
    db: DbSessionDep,
):
    return block_review(db, user_id=user_id, admin_user_id=admin_user.id)


@router.post("/clickup/sync", response_model=MembershipClickupSyncResponse)
def sync_clickup_reviews(
    admin_user: AdminUserDep,
    db: DbSessionDep,
):
    del admin_user
    try:
        synced = sync_clickup_directory(db)
    except ClickupConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": str(exc),
                "code": "CLICKUP_CONFIG_MISSING",
                "missing_envs": exc.missing_envs,
            },
        ) from exc
    except ClickupFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "detail": str(exc),
                "code": "CLICKUP_SYNC_FAILED",
                "clickup_status_code": exc.status_code,
            },
        ) from exc

    return MembershipClickupSyncResponse(synced=synced)
