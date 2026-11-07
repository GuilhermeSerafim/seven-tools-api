import logging

import pytest

from app.modules.email import service


@pytest.fixture(autouse=True)
def setup_db():
    yield


def test_build_password_reset_email_escapes_html_href_and_keeps_text_url_raw():
    reset_url = 'https://app.example.com/redefinir-senha?token=abc&next="bad"'

    _subject, html, text = service.build_password_reset_email(reset_url)

    assert 'href="https://app.example.com/redefinir-senha?token=abc&amp;next=&quot;bad&quot;"' in html
    assert f"Acesse: {reset_url}" in text


def test_log_provider_emits_visible_dev_reset_link(monkeypatch, caplog):
    reset_url = "https://app.example.com/redefinir-senha?token=abc"

    monkeypatch.setattr(service.settings, "email_provider", "log")

    with caplog.at_level(logging.WARNING):
        service.send_password_reset_email("test@example.com", reset_url)

    assert "DEV password reset link for test@example.com" in caplog.text
    assert reset_url in caplog.text


def test_resend_provider_posts_transactional_email(monkeypatch):
    calls: list[dict] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(service.settings, "email_provider", "resend")
    monkeypatch.setattr(service.settings, "resend_api_key", "re_key_123")
    monkeypatch.setattr(service.settings, "email_from", "SEVEN Tools <no-reply@example.com>")
    monkeypatch.setattr(service.httpx, "post", fake_post)

    service.send_password_reset_email("test@example.com", "https://app.example.com/redefinir-senha?token=abc")

    assert calls == [
        {
            "url": "https://api.resend.com/emails",
            "headers": {"Authorization": "Bearer re_key_123", "Content-Type": "application/json"},
            "json": {
                "from": "SEVEN Tools <no-reply@example.com>",
                "to": ["test@example.com"],
                "subject": "Redefinicao de senha - SEVEN Tools",
                "html": '<p>Recebemos uma solicitacao para redefinir sua senha no SEVEN Tools.</p><p><a href="https://app.example.com/redefinir-senha?token=abc">Redefinir senha</a></p><p>Se voce nao solicitou esta alteracao, ignore este e-mail.</p>',
                "text": "Recebemos uma solicitacao para redefinir sua senha no SEVEN Tools.\n\nAcesse: https://app.example.com/redefinir-senha?token=abc\n\nSe voce nao solicitou esta alteracao, ignore este e-mail.",
            },
            "timeout": 10.0,
        }
    ]


def test_resend_provider_without_api_key_logs_warning_and_does_not_post(monkeypatch, caplog):
    calls: list[dict] = []

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr(service.settings, "email_provider", "resend")
    monkeypatch.setattr(service.settings, "resend_api_key", "")
    monkeypatch.setattr(service.httpx, "post", fake_post)

    service.send_password_reset_email("test@example.com", "https://app.example.com/redefinir-senha?token=abc")

    assert calls == []
    assert "RESEND_API_KEY is not configured" in caplog.text


def test_resend_provider_failure_is_logged_without_raising(monkeypatch, caplog):
    class FakeResponse:
        def raise_for_status(self) -> None:
            raise service.httpx.HTTPStatusError(
                "boom",
                request=service.httpx.Request("POST", "https://api.resend.com/emails"),
                response=service.httpx.Response(500),
            )

    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        return FakeResponse()

    monkeypatch.setattr(service.settings, "email_provider", "resend")
    monkeypatch.setattr(service.settings, "resend_api_key", "re_key_123")
    monkeypatch.setattr(service.httpx, "post", fake_post)

    with caplog.at_level(logging.WARNING):
        service.send_password_reset_email("test@example.com", "https://app.example.com/redefinir-senha?token=abc")

    assert "Password reset email delivery failed" in caplog.text
