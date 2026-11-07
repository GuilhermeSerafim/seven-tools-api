from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_db
from app.modules.clickup.service import ClickupConfigurationError, ClickupFetchError
from app.modules.companies.service import list_registration_companies_with_sync
from app.schemas.company import RegistrationCompanyOptionsResponse

router = APIRouter(prefix="/companies", tags=["companies"])

DbSessionDep = Annotated[DbSession, Depends(get_db)]


@router.get("/registration-options", response_model=RegistrationCompanyOptionsResponse)
def get_registration_options(db: DbSessionDep):
    try:
        items = list_registration_companies_with_sync(db)
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

    return RegistrationCompanyOptionsResponse(items=items)
