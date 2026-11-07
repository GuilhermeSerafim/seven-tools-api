import logging
from html import escape

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def build_password_reset_email(reset_url: str) -> tuple[str, str, str]:
    subject = "Redefinicao de senha - SEVEN Tools"
    escaped_reset_url = escape(reset_url, quote=True)
    html = (
        "<p>Recebemos uma solicitacao para redefinir sua senha no SEVEN Tools.</p>"
        f'<p><a href="{escaped_reset_url}">Redefinir senha</a></p>'
        "<p>Se voce nao solicitou esta alteracao, ignore este e-mail.</p>"
    )
    text = (
        "Recebemos uma solicitacao para redefinir sua senha no SEVEN Tools.\n\n"
        f"Acesse: {reset_url}\n\n"
        "Se voce nao solicitou esta alteracao, ignore este e-mail."
    )
    return subject, html, text


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    if settings.email_provider == "log":
        logger.warning("DEV password reset link for %s: %s", to_email, reset_url)
        return

    if settings.email_provider == "resend":
        if not settings.resend_api_key:
            logger.warning("RESEND_API_KEY is not configured; password reset email was not sent.")
            return
        subject, html, text = build_password_reset_email(reset_url)
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.email_from,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                    "text": text,
                },
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Password reset email delivery failed.", exc_info=True)
        return

    logger.warning(
        "Email provider %s is not configured for password reset. No password reset email was sent.",
        settings.email_provider,
    )
