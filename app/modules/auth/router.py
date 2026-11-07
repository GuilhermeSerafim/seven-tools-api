# seven_tools_api/app/modules/auth/router.py
from datetime import datetime, timezone

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session as DbSession

from app.dependencies import get_current_user, get_db
from app.models.session import Session
from app.models.user import User
from app.modules.auth.password_reset import (
    GENERIC_RESET_REQUEST_DETAIL,
    confirm_password_reset,
    request_password_reset,
)
from app.modules.auth.service import authenticate, change_password, invalidate_session, register_user
from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
)

CurrentUserDep = Annotated[User, Depends(get_current_user)]
DbSessionDep = Annotated[DbSession, Depends(get_db)]

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession = Depends(get_db)):
    user, token_or_error = register_user(
        db,
        name=body.name,
        email=body.email,
        password=body.password,
        company_id=body.company_id,
        other_company_name=body.other_company_name,
        other_company_cnpj=body.other_company_cnpj,
    )
    if user is None:
        if token_or_error == "COMPANY_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Empresa não encontrada.", "code": token_or_error},
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "E-mail já cadastrado.", "code": token_or_error},
        )
    return AuthResponse(
        token=token_or_error,
        user=AuthUserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: DbSession = Depends(get_db)):
    user, token = authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "E-mail ou senha inválidos.", "code": "INVALID_CREDENTIALS"},
        )
    return AuthResponse(
        token=token,
        user=AuthUserResponse.model_validate(user),
    )


@router.post("/logout")
def logout(
    authorization: str = Header(...),
    db: DbSession = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cabeçalho de autorização inválido.")

    token = authorization.removeprefix("Bearer ")

    session = db.query(Session).filter(Session.token == token).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")

    if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada.")

    invalidate_session(db, token)
    return {"detail": "Sessão encerrada com sucesso."}


@router.post("/password-reset/request")
@limiter.limit("3/minute")
def request_password_reset_endpoint(
    request: Request,
    body: PasswordResetRequest,
    db: DbSessionDep,
):
    request_password_reset(db, body.email)
    return {"detail": GENERIC_RESET_REQUEST_DETAIL}


@router.post("/password-reset/confirm")
@limiter.limit("5/minute")
def confirm_password_reset_endpoint(
    request: Request,
    body: PasswordResetConfirmRequest,
    db: DbSessionDep,
):
    if not confirm_password_reset(db, body.token, body.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Link invalido ou expirado. Solicite uma nova recuperacao.",
                "code": "INVALID_OR_EXPIRED_RESET_TOKEN",
            },
        )
    return {"detail": "Senha redefinida com sucesso."}


@router.post("/change-password")
def change_password_endpoint(
    body: ChangePasswordRequest,
    user: CurrentUserDep,
    db: DbSessionDep,
):
    if not change_password(db, user, body.current_password, body.new_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Senha atual inválida.", "code": "INVALID_CURRENT_PASSWORD"},
        )
    return {"detail": "Senha alterada com sucesso."}
