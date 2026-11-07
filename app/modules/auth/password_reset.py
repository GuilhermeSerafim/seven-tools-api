import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.models.session import Session
from app.models.user import User
from app.modules.email.service import send_password_reset_email
from app.utils.security import hash_password


GENERIC_RESET_REQUEST_DETAIL = "Se este e-mail estiver cadastrado, enviaremos instrucoes para redefinir sua senha."

logger = logging.getLogger(__name__)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def request_password_reset(db: DbSession, email: str) -> None:
    normalized_email = email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if user is None:
        return

    now = datetime.now(timezone.utc)
    (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .update({"used_at": now}, synchronize_session=False)
    )

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_reset_token(token),
        expires_at=now + timedelta(minutes=settings.password_reset_token_ttl_minutes),
    )
    db.add(reset_token)
    reset_url = f"{settings.frontend_base_url.rstrip('/')}/redefinir-senha?token={token}"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return

    try:
        send_password_reset_email(user.email, reset_url)
    except Exception:
        logger.warning("Password reset email delivery failed for %s.", user.email, exc_info=True)


def is_expired(expires_at: datetime, now: datetime) -> bool:
    return expires_at.replace(tzinfo=timezone.utc) < now


def confirm_password_reset(db: DbSession, token: str, new_password: str) -> bool:
    now = datetime.now(timezone.utc)
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == hash_reset_token(token))
        .with_for_update()
        .first()
    )
    if reset_token is None:
        return False
    if reset_token.used_at is not None:
        return False
    if is_expired(reset_token.expires_at, now):
        return False

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if user is None:
        return False

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    reset_token.used_at = now
    db.query(Session).filter(Session.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return True
