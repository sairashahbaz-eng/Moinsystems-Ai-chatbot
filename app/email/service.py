import os
import smtplib
from email.message import EmailMessage


class EmailService:
    """SMTP email service abstraction."""

    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "")
        self.email_to = os.getenv(
            "EMAIL_TO",
            "info@moinsystemsai.com",
        )

    def send(
        self,
        subject: str,
        body: str,
    ) -> dict[str, str | bool | None]:
        """Send an email through the configured SMTP server."""

        if not self.smtp_host:
            return {
                "success": False,
                "provider_message_id": None,
                "error": "SMTP host is not configured.",
            }

        if not self.email_from:
            return {
                "success": False,
                "provider_message_id": None,
                "error": "Sender email is not configured.",
            }

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.email_from
        message["To"] = self.email_to
        message.set_content(body)

        try:
            with smtplib.SMTP(
                self.smtp_host,
                self.smtp_port,
                timeout=20,
            ) as server:
                server.starttls()

                if self.smtp_username and self.smtp_password:
                    server.login(
                        self.smtp_username,
                        self.smtp_password,
                    )

                server.send_message(message)

            return {
                "success": True,
                "provider_message_id": None,
                "error": None,
            }

        except (smtplib.SMTPException, OSError) as exc:
            return {
                "success": False,
                "provider_message_id": None,
                "error": str(exc)[:500],
            }


email_service = EmailService()