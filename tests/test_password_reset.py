import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.password_reset_token import PasswordResetToken
from app.models.session import Session
from app.modules.auth.password_reset import (
    confirm_password_reset,
    hash_reset_token,
    request_password_reset,
)
from app.modules.email import service as email_service
from app.modules.email.service import send_password_reset_email
from app.utils.security import hash_password
from tests.support import NEW_SECRET, SEEDED_SECRET, WRONG_SECRET, with_secret


GENERIC_DETAIL = "Se este e-mail estiver cadastrado, enviaremos instrucoes para redefinir sua senha."


def extract_token(reset_url: str) -> str:
    parsed = urlparse(reset_url)
    values = parse_qs(parsed.query).get("token")
    assert values is not None
    assert len(values) == 1
    return values[0]


def request_reset_token(client, monkeypatch, email: str = "test@example.com") -> str:
    sent: list[dict[str, str]] = []

    def fake_send_password_reset_email(to_email: str, reset_url: str) -> None:
        sent.append({"to_email": to_email, "reset_url": reset_url})

    monkeypatch.setattr(
        "app.modules.auth.password_reset.send_password_reset_email",
        fake_send_password_reset_email,
    )
    response = client.post("/api/v1/auth/password-reset/request", json={"email": email})
    assert response.status_code == 200
    assert len(sent) == 1
    return extract_token(sent[0]["reset_url"])


def test_password_reset_request_is_generic_for_unknown_email(client, db):
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nobody@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": GENERIC_DETAIL}
    assert db.query(PasswordResetToken).count() == 0


def test_password_reset_request_creates_hashed_token_for_known_email(client, db, sample_user, monkeypatch):
    sent: list[dict[str, str]] = []

    def fake_send_password_reset_email(to_email: str, reset_url: str) -> None:
        sent.append({"to_email": to_email, "reset_url": reset_url})

    monkeypatch.setattr(
        "app.modules.auth.password_reset.send_password_reset_email",
        fake_send_password_reset_email,
    )
    monkeypatch.setattr("app.modules.auth.password_reset.settings.frontend_base_url", "http://localhost:5173")

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": " TEST@EXAMPLE.COM "},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": GENERIC_DETAIL}
    assert len(sent) == 1
    assert sent[0]["to_email"] == "test@example.com"
    assert sent[0]["reset_url"].startswith("http://localhost:5173/redefinir-senha?token=")

    token = extract_token(sent[0]["reset_url"])
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == sample_user.id).one()
    assert reset_token.token_hash == hash_reset_token(token)
    assert reset_token.token_hash != token
    assert reset_token.used_at is None
    assert reset_token.expires_at is not None


def test_password_reset_request_commits_token_before_sending_email(client, db, sample_user, monkeypatch):
    committed = False
    sent: list[dict[str, str]] = []
    original_commit = db.commit

    def commit_and_record() -> None:
        nonlocal committed
        original_commit()
        committed = True

    def fake_send_password_reset_email(to_email: str, reset_url: str) -> None:
        assert committed is True
        sent.append({"to_email": to_email, "reset_url": reset_url})

    monkeypatch.setattr(db, "commit", commit_and_record)
    monkeypatch.setattr(
        "app.modules.auth.password_reset.send_password_reset_email",
        fake_send_password_reset_email,
    )
    monkeypatch.setattr("app.modules.auth.password_reset.settings.frontend_base_url", "http://localhost:5173///")

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": sample_user.email},
    )

    assert response.status_code == 200
    assert len(sent) == 1
    assert sent[0]["reset_url"].startswith("http://localhost:5173/redefinir-senha?token=")


def test_password_reset_request_replaces_previous_unused_token(client, db, sample_user, monkeypatch):
    sent: list[str] = []

    def fake_send_password_reset_email(to_email: str, reset_url: str) -> None:
        sent.append(reset_url)

    monkeypatch.setattr(
        "app.modules.auth.password_reset.send_password_reset_email",
        fake_send_password_reset_email,
    )

    first_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": sample_user.email},
    )
    first_token = extract_token(sent[0])

    second_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": sample_user.email},
    )
    second_token = extract_token(sent[1])

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_token != second_token

    reset_tokens = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == sample_user.id)
        .order_by(PasswordResetToken.created_at.asc())
        .all()
    )
    assert len(reset_tokens) == 2
    assert reset_tokens[0].token_hash == hash_reset_token(first_token)
    assert reset_tokens[0].used_at is not None
    assert reset_tokens[1].token_hash == hash_reset_token(second_token)
    assert reset_tokens[1].used_at is None


def test_unsupported_email_provider_warns_no_password_reset_email_sent(monkeypatch):
    warnings: list[tuple[str, tuple[object, ...]]] = []

    def fake_warning(message: str, *args: object, **kwargs: object) -> None:
        warnings.append((message, args))

    monkeypatch.setattr("app.modules.email.service.settings.email_provider", "smtp")
    monkeypatch.setattr(email_service.logger, "warning", fake_warning)

    send_password_reset_email("test@example.com", "http://localhost/reset?token=abc")

    assert warnings == [
        (
            "Email provider %s is not configured for password reset. No password reset email was sent.",
            ("smtp",),
        )
    ]


def test_password_reset_delivery_failure_still_returns_generic_response(client, db, sample_user, monkeypatch):
    def fake_send_password_reset_email(to_email: str, reset_url: str) -> None:
        raise RuntimeError("delivery unavailable")

    monkeypatch.setattr(
        "app.modules.auth.password_reset.send_password_reset_email",
        fake_send_password_reset_email,
    )

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": sample_user.email},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": GENERIC_DETAIL}
    assert db.query(PasswordResetToken).filter(PasswordResetToken.user_id == sample_user.id).count() == 1


def test_password_reset_allows_only_one_unused_token_per_user(db, sample_user):
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.add(
        PasswordResetToken(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            token_hash=hash_reset_token("first-token"),
            expires_at=expires_at,
        )
    )
    db.commit()

    db.add(
        PasswordResetToken(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            token_hash=hash_reset_token("manual-token"),
            expires_at=expires_at,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


def test_password_reset_service_rolls_back_and_skips_delivery_on_integrity_error(db, sample_user, monkeypatch):
    rolled_back: list[bool] = []
    sent: list[dict[str, str]] = []

    def fake_commit() -> None:
        raise IntegrityError("statement", {}, RuntimeError("duplicate token"))

    def fake_rollback() -> None:
        rolled_back.append(True)

    def fake_send_password_reset_email(to_email: str, reset_url: str) -> None:
        sent.append({"to_email": to_email, "reset_url": reset_url})

    monkeypatch.setattr(db, "commit", fake_commit)
    monkeypatch.setattr(db, "rollback", fake_rollback)
    monkeypatch.setattr(
        "app.modules.auth.password_reset.send_password_reset_email",
        fake_send_password_reset_email,
    )

    request_password_reset(db, sample_user.email)

    assert rolled_back == [True]
    assert sent == []


def test_password_reset_confirm_changes_password_and_consumes_token(client, db, sample_user, monkeypatch):
    token = request_reset_token(client, monkeypatch)

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": NEW_SECRET},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": "Senha redefinida com sucesso."}

    db.refresh(sample_user)
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == sample_user.id).one()
    assert reset_token.used_at is not None
    assert sample_user.must_change_password is False

    old_login = client.post(
        "/api/v1/auth/login",
        json=with_secret({"email": "test@example.com"}, SEEDED_SECRET),
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json=with_secret({"email": "test@example.com"}, NEW_SECRET),
    )
    assert new_login.status_code == 200


def test_password_reset_confirm_rejects_reused_token(client, sample_user, monkeypatch):
    token = request_reset_token(client, monkeypatch)
    first = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": NEW_SECRET},
    )
    second = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": WRONG_SECRET},
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"]["code"] == "INVALID_OR_EXPIRED_RESET_TOKEN"


def test_password_reset_confirm_rejects_expired_token(client, db, sample_user, monkeypatch):
    token = request_reset_token(client, monkeypatch)
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == sample_user.id).one()
    reset_token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": NEW_SECRET},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_OR_EXPIRED_RESET_TOKEN"


def test_password_reset_confirm_invalidates_existing_sessions(client, db, sample_user, auth_token, monkeypatch):
    assert db.query(Session).filter(Session.token == auth_token).count() == 1
    token = request_reset_token(client, monkeypatch)

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": NEW_SECRET},
    )

    assert response.status_code == 200
    assert db.query(Session).filter(Session.user_id == sample_user.id).count() == 0


def test_new_password_reset_request_invalidates_previous_unused_token(client, db, sample_user, monkeypatch):
    first_token = request_reset_token(client, monkeypatch)
    second_token = request_reset_token(client, monkeypatch)

    reset_tokens = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == sample_user.id)
        .order_by(PasswordResetToken.created_at.asc())
        .all()
    )
    assert len(reset_tokens) == 2
    assert reset_tokens[0].token_hash == hash_reset_token(first_token)
    assert reset_tokens[0].used_at is not None
    assert reset_tokens[1].token_hash == hash_reset_token(second_token)
    assert reset_tokens[1].used_at is None

    first_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": first_token, "new_password": NEW_SECRET},
    )
    second_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": second_token, "new_password": NEW_SECRET},
    )

    assert first_response.status_code == 400
    assert first_response.json()["detail"]["code"] == "INVALID_OR_EXPIRED_RESET_TOKEN"
    assert second_response.status_code == 200


def test_password_reset_confirm_allows_single_concurrent_token_use(
    client,
    db,
    test_engine,
    sample_user,
    monkeypatch,
):
    token = request_reset_token(client, monkeypatch)

    def slow_hash_password(password: str) -> str:
        time.sleep(0.2)
        return hash_password(password)

    monkeypatch.setattr(
        "app.modules.auth.password_reset.hash_password",
        slow_hash_password,
    )
    SessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    def confirm_with_independent_session() -> bool:
        thread_db = SessionLocal()
        try:
            return confirm_password_reset(thread_db, token, NEW_SECRET)
        finally:
            thread_db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(confirm_with_independent_session) for _ in range(2)]
        results = [future.result() for future in futures]

    assert sorted(results) == [False, True]

    db.expire_all()
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == sample_user.id
    ).one()
    assert reset_token.used_at is not None


def test_password_reset_request_is_rate_limited(client):
    responses = [
        client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "nobody@example.com"},
        )
        for _ in range(4)
    ]

    assert [response.status_code for response in responses[:3]] == [200, 200, 200]
    assert responses[3].status_code == 429
