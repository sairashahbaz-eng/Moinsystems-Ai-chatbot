import os
import smtplib
import time
from email.message import EmailMessage
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class EmailService:

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "").strip()
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME", "").strip()
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "").strip()
        self.email_to = os.getenv(
            "EMAIL_TO",
            "info@moinsystemsai.com",
        ).strip()

    def send_lead_notification(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        if not self.host:
            return {
                "success": False,
                "provider_message_id": None,
                "error": "SMTP is not configured.",
            }

        if not self.email_from:
            return {
                "success": False,
                "provider_message_id": None,
                "error": "EMAIL_FROM is not configured.",
            }

        message = self._build_message(payload)

        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                with smtplib.SMTP(
                    self.host,
                    self.port,
                    timeout=15,
                ) as smtp:

                    smtp.starttls()

                    if self.username and self.password:
                        smtp.login(
                            self.username,
                            self.password,
                        )

                    smtp.send_message(message)

                return {
                    "success": True,
                    "provider_message_id": message.get(
                        "Message-ID"
                    ),
                    "error": None,
                }

            except (smtplib.SMTPException, OSError) as exc:
                last_error = self._sanitize_error(exc)

                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY_SECONDS)

        return {
            "success": False,
            "provider_message_id": None,
            "error": last_error or "Email delivery failed.",
        }

    def _build_message(
        self,
        payload: dict[str, Any],
    ) -> EmailMessage:

        message = EmailMessage()

        message["Subject"] = (
            "New MoinSystems AI Lead Submission"
        )

        message["From"] = self.email_from
        message["To"] = self.email_to

        message.set_content(
            self._format_payload(payload)
        )

        return message

    @staticmethod
    def _format_payload(
        payload: dict[str, Any],
    ) -> str:

        fields = [
            ("Name", payload.get("full_name")),
            ("Email", payload.get("email")),
            ("Contact Number", payload.get("contact_number")),
            ("Company", payload.get("company_name")),
            ("Service Interest", payload.get("service_interest")),
            ("Project Summary", payload.get("project_summary")),
            ("Timeline", payload.get("timeline")),
            ("Budget Range", payload.get("budget_range")),
            ("Source Page", payload.get("source_page")),
            ("User Question", payload.get("user_question")),
            (
                "Conversation Summary",
                payload.get("conversation_summary"),
            ),
            ("Timestamp", payload.get("timestamp")),
        ]

        lines = [
            "New lead received from the MoinSystems AI chatbot.",
            "",
        ]

        for label, value in fields:
            if value is not None and str(value).strip():
                lines.append(
                    f"{label}: {str(value).strip()}"
                )

        return "\n".join(lines)

    @staticmethod
    def _sanitize_error(
        exc: Exception,
    ) -> str:

        error = str(exc)

        sensitive_values = [
            os.getenv("SMTP_PASSWORD", ""),
            os.getenv("GEMINI_API_KEY", ""),
        ]

        for value in sensitive_values:
            if value:
                error = error.replace(
                    value,
                    "[REDACTED]",
                )

        return error[:500]


email_service = EmailService()