import smtplib
from email.message import EmailMessage

from app.config import get_settings


class EmailNotifier:
    def __init__(self) -> None:
        self._settings = get_settings()

    def send(self, to_address: str, subject: str, body: str) -> None:
        if not self._settings.smtp_host or not self._settings.smtp_from_address:
            raise RuntimeError("SMTP is not configured")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._settings.smtp_from_address
        message["To"] = to_address
        message.set_content(body)

        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port) as smtp:
            if self._settings.smtp_use_tls:
                smtp.starttls()
            if self._settings.smtp_username and self._settings.smtp_password:
                smtp.login(self._settings.smtp_username, self._settings.smtp_password)
            smtp.send_message(message)
