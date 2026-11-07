# seven_tools_api/app/modules/ai/router.py
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_approved_user, get_db
from app.models.user import User
from app.modules.ai.schemas import (
    CommercialDiagnosisAssistantRequest,
    CommercialDiagnosisAssistantResponse,
    LeadQualificationAssistantRequest,
    LeadQualificationAssistantResponse,
    ProposalAssistantRequest,
    ProposalAssistantResponse,
)
from app.modules.ai.service import (
    commercial_diagnosis_assistant_turn,
    diagnose,
    lead_qualification_assistant_turn,
    proposal_assistant_turn,
)
from app.schemas.ai import DiagnoseRequest, DiagnoseResponse

router = APIRouter(prefix="/ai", tags=["ai"])


def _require_authorization_header(authorization: str | None = Header(default=None)):
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def _parse_retry_after_seconds(retry_after: str | None) -> int | None:
    if retry_after is None:
        return None
    try:
        seconds = int(retry_after)
    except ValueError:
        return None
    return seconds if seconds > 0 else None


@router.post("/diagnose", response_model=DiagnoseResponse)
def run_diagnose(
    body: DiagnoseRequest,
    user: User = Depends(get_current_approved_user),
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


@router.post(
    "/proposal-assistant",
    response_model=ProposalAssistantResponse,
    dependencies=[Depends(_require_authorization_header)],
    responses={
        429: {"description": "Provider rate limit reached"},
        502: {"description": "Provider authentication or gateway error"},
        504: {"description": "Provider timeout or unavailable"},
    },
)
def proposal_assistant_endpoint(
    req: ProposalAssistantRequest,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_approved_user),
) -> ProposalAssistantResponse:
    try:
        return proposal_assistant_turn(db, user, req)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 429:
            raise HTTPException(
                status_code=429,
                detail={
                    "detail": "rate_limited",
                    "retry_after_s": _parse_retry_after_seconds(
                        exc.response.headers.get("retry-after"),
                    ),
                },
            )
        if status_code in (401, 403):
            raise HTTPException(status_code=502, detail="provider_error")
        if status_code >= 500:
            raise HTTPException(status_code=504, detail="provider_unavailable")
        raise HTTPException(status_code=status_code, detail="provider_error")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="provider_unavailable")


@router.post(
    "/commercial-diagnosis-assistant",
    response_model=CommercialDiagnosisAssistantResponse,
    dependencies=[Depends(_require_authorization_header)],
    responses={
        429: {"description": "Provider rate limit reached"},
        502: {"description": "Provider authentication or gateway error"},
        504: {"description": "Provider timeout or unavailable"},
    },
)
def commercial_diagnosis_assistant_endpoint(
    req: CommercialDiagnosisAssistantRequest,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_approved_user),
) -> CommercialDiagnosisAssistantResponse:
    try:
        return commercial_diagnosis_assistant_turn(db, user, req)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 429:
            raise HTTPException(
                status_code=429,
                detail={
                    "detail": "rate_limited",
                    "retry_after_s": _parse_retry_after_seconds(
                        exc.response.headers.get("retry-after"),
                    ),
                },
            )
        if status_code in (401, 403):
            raise HTTPException(status_code=502, detail="provider_error")
        if status_code >= 500:
            raise HTTPException(status_code=504, detail="provider_unavailable")
        raise HTTPException(status_code=status_code, detail="provider_error")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="provider_unavailable")


@router.post(
    "/lead-qualification-assistant",
    response_model=LeadQualificationAssistantResponse,
    dependencies=[Depends(_require_authorization_header)],
    responses={
        429: {"description": "Provider rate limit reached"},
        502: {"description": "Provider authentication or gateway error"},
        504: {"description": "Provider timeout or unavailable"},
    },
)
def lead_qualification_assistant_endpoint(
    req: LeadQualificationAssistantRequest,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_approved_user),
) -> LeadQualificationAssistantResponse:
    try:
        return lead_qualification_assistant_turn(db, user, req)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 429:
            raise HTTPException(
                status_code=429,
                detail={
                    "detail": "rate_limited",
                    "retry_after_s": _parse_retry_after_seconds(
                        exc.response.headers.get("retry-after"),
                    ),
                },
            )
        if status_code in (401, 403):
            raise HTTPException(status_code=502, detail="provider_error")
        if status_code >= 500:
            raise HTTPException(status_code=504, detail="provider_unavailable")
        raise HTTPException(status_code=status_code, detail="provider_error")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="provider_unavailable")
