# app/utils/email.py

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Optional, List, Dict, Any
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Centralized AWS SES email service."""

    def __init__(self):
        self.client = boto3.client(
            "ses",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.sender_email = settings.ses_sender_email
        self.sender_name = settings.ses_sender_name

        # Setup Jinja2 for template rendering
        template_dir = Path(__file__).parent / "modules"
        self.jinja_env = Environment(
            loader=FileSystemLoader(searchpath=str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render email template with context."""
        try:
            template = self.jinja_env.get_template(template_path)
            return template.render(**context)
        except Exception as e:
            logger.error("template_render_error", template_path=template_path, error=str(e))
            raise

    async def send_email(
        self, to_emails: List[str], subject: str, body_html: Optional[str] = None,
        body_text: Optional[str] = None, cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None, attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via AWS SES.

        Args:
            to_emails (List[str]): List of recipient email addresses.
            subject (str): Subject of the email.
            body_html (Optional[str]): HTML body of the email.
            body_text (Optional[str]): Plain text body of the email.
            cc_emails (Optional[List[str]]): List of CC email addresses.
            bcc_emails (Optional[List[str]]): List of BCC email addresses.
            attachments (Optional[List[Dict[str, Any]]]): List of attachments with 'filename' and 'content'.
            reply_to (Optional[List[str]]): List of reply-to email addresses.

        Returns:
            Dict with message ID and status.
        """
        try:
            # Create message
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = ", ".join(to_emails)

            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)

            if reply_to:
                msg["Reply-To"] = ", ".join(reply_to)

            # Create body
            body = MIMEMultipart("alternative")

            if body_text:
                body.attach(MIMEText(body_text, "plain", "utf-8"))

            if body_html:
                body.attach(MIMEText(body_html, "html", "utf-8"))

            msg.attach(body)

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(attachment["content"])
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=attachment["filename"]
                    )
                    msg.attach(part)

            # Combine all recipients
            destinations = to_emails.copy()
            if cc_emails:
                destinations.extend(cc_emails)
            if bcc_emails:
                destinations.extend(bcc_emails)

            # Send email
            response = self.client.send_raw_email(
                Source=self.sender_email,
                Destinations=destinations,
                RawMessage={"Data": msg.as_string()}
            )

            logger.info(
                "email_sent", message_id=response["MessageId"],
                to=to_emails, subject=subject
            )

            return {
                "message_id": response["MessageId"],
                "status": "sent"
            }
        
        except ClientError as e:
            logger.error(
                "ses_send_error", error=str(e),
                error_code=e.response["Error"]["Code"]
            )
            raise
        except Exception as e:
            logger.error("email_send_error", error=str(e))
            raise

    async def send_templated_email(
        self, to_emails: List[str], subject: str, template_path: str,
        context: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Send email using a template."""
        html_content = self.render_template(template_path, context)
        return await self.send_email(
            to_emails=to_emails,
            subject=subject,
            body_html=html_content,
            **kwargs
        )
    

email_service = EmailService()
