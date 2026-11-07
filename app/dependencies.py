# seven_tools_api/app/dependencies.py
from datetime import datetime, timedelta, timezone
from typing import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.database import SessionLocal
from app.models.session import Session
from app.models.user import User


def get_db() -> Generator[DbSession, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _error(status_code: int, detail: str, code: str):
    """Raise HTTPException with spec-compliant body: {detail, code}."""
    raise HTTPException(status_code=status_code, detail={"detail": detail, "code": code})


def get_current_user(
    authorization: str = Header(...),
    db: DbSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        _error(status.HTTP_401_UNAUTHORIZED, "Cabeçalho de autorização inválido.", "INVALID_AUTH")

    token = authorization.removeprefix("Bearer ")

    session = db.query(Session).filter(Session.token == token).first()
    if session is None:
        _error(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.", "INVALID_SESSION")

    now = datetime.now(timezone.utc)
    if session.expires_at.replace(tzinfo=timezone.utc) < now:
        db.delete(session)
        db.commit()
        _error(status.HTTP_401_UNAUTHORIZED, "Sessão expirada.", "SESSION_EXPIRED")

    # Sliding expiration
    session.expires_at = now + timedelta(days=settings.session_ttl_days)
    db.commit()

    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None:
        _error(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado.", "USER_NOT_FOUND")

    return user


def get_current_approved_user(user: User = Depends(get_current_user)) -> User:
    if user.validation_status.value == "pending_review":
        _error(status.HTTP_403_FORBIDDEN, "Validação de membro pendente.", "VALIDATION_PENDING")
    if user.validation_status.value == "blocked":
        _error(status.HTTP_403_FORBIDDEN, "Membro bloqueado.", "MEMBERSHIP_BLOCKED")
    return user


def get_current_admin(user: User = Depends(get_current_approved_user)) -> User:
    if user.role.value != "admin":
        _error(status.HTTP_403_FORBIDDEN, "Acesso de administrador obrigatório.", "ADMIN_REQUIRED")
    return user
