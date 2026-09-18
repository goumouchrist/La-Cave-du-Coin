import smtplib
from email.message import EmailMessage

from app.config import settings


class MailNotConfiguredError(Exception):
    pass


class MailSendError(Exception):
    pass


def send_email(to: str, subject: str, body: str, attachment: tuple[str, bytes, str] | None = None) -> None:
    """Envoie un email simple, avec une pièce jointe optionnelle (filename, bytes, mime_subtype, ex. 'pdf')."""
    if not settings.SMTP_HOST:
        raise MailNotConfiguredError("Aucun serveur SMTP configuré (SMTP_HOST vide dans .env)")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM or settings.SMTP_USER
    message["To"] = to
    message.set_content(body)

    if attachment:
        filename, content, mime_subtype = attachment
        message.add_attachment(content, maintype="application", subtype=mime_subtype, filename=filename)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailSendError(f"Échec de l'envoi de l'email : {exc}") from exc
