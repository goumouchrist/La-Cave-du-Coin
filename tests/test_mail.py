import pytest

from app.config import settings
from app.services import mail as mail_service


def test_send_email_raises_when_smtp_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    with pytest.raises(mail_service.MailNotConfiguredError):
        mail_service.send_email("client@example.com", "Sujet", "Corps du message")


def test_send_email_uses_smtp_and_attaches_pdf(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_USER", "boutique@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(settings, "SMTP_FROM", "boutique@example.com")

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            sent["host"] = host
            sent["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def starttls(self):
            sent["starttls"] = True

        def login(self, user, password):
            sent["login"] = (user, password)

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setattr(mail_service.smtplib, "SMTP", FakeSMTP)

    mail_service.send_email(
        "client@example.com", "Reçu VT-0001", "Merci pour votre achat.",
        attachment=("recu_VT-0001.pdf", b"%PDF-fake", "pdf"),
    )

    assert sent["host"] == "smtp.example.com"
    assert sent["starttls"] is True
    assert sent["login"] == ("boutique@example.com", "secret")
    message = sent["message"]
    assert message["To"] == "client@example.com"
    assert message["Subject"] == "Reçu VT-0001"
    assert message.is_multipart()


def test_send_email_wraps_smtp_errors(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")

    class FailingSMTP:
        def __init__(self, host, port, timeout=None):
            pass

        def __enter__(self):
            raise OSError("connection refused")

        def __exit__(self, *exc_info):
            return False

    monkeypatch.setattr(mail_service.smtplib, "SMTP", FailingSMTP)

    with pytest.raises(mail_service.MailSendError):
        mail_service.send_email("client@example.com", "Sujet", "Corps du message")
