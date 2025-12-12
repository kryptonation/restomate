# src/common/email_service.py

"""
Production-grade Amazon SES Email Service
Supports template rendering, attachments, inline images, and comprehensive error handling
Follows AWS best practices for email deliverability and sender reputation
"""

import base64
import mimetypes
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from jinja2 import (
    Environment, FileSystemLoader, PackageLoader, select_autoescape,
    TemplateNotFound
)

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class EmailAttachment:
    """
    Represents an email attachment with metadata.
    """

    def __init__(
        self, filename: str, content: Union[bytes, str], content_type: Optional[str] = None,
        disposition: str = "attachment", content_id: Optional[str] = None
    ):
        """
        Initialize email attachment

        Args:
            filename: Name of the file as it will appear in the email
            content: File content as bytes or base64 string
            content_type: MIME type (auto-detected if not provided)
            disposition: 'attachment' or 'inline' for embedded images
            content_id: Content ID for inline images (cid reference)
        """
        self.filename = filename
        self.content = content if isinstance(content, bytes) else base64.b64decode(content)
        self.content_type = content_type or self._detect_content_type()
        self.disposition = disposition
        self.content_id = content_id or str(uuid4())

    def _detect_content_type(self) -> str:
        """Detect MIME type from filename"""
        mime_type, _ = mimetypes.guess_type(self.filename)
        return mime_type or "application/octet-stream"
    
    @classmethod
    def from_file(
        cls, filepath: Union[str, Path], filename: Optional[str] = None,
        disposition: str = "attachment", content_id: Optional[str] = None,
    ) -> "EmailAttachment":
        """
        Create attachment from file path

        Args:
            filepath: Path to the file
            filename: Override filename (uses actual file name if not provided)
            disposition: 'attachment' or 'inline'
            content_id: Content ID for inline images
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Attachment file not found: {filepath}")
        
        with open(filepath, "rb") as f:
            content = f.read()

        return cls(
            filename=filename or filepath.name,
            content=content,
            disposition=disposition,
            content_id=content_id
        )
    

class EmailTemplate:
    """
    Email template with subject, HTML, and plain text
    """

    def __init__(
        self, subject: str, html_body: Optional[str] = None, text_body: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize email template

        Args:
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text email body (fallback)
            context: Template variables for rendering
        """
        self.subject = subject
        self.html_body = html_body
        self.text_body = text_body
        self.context = context or {}


class SESEmailService:
    """
    Production-grade Amazon SES Email Service

    Features:
    - Jinja2 template rendering with autoescaping
    - Multiple attachments support (up to 10MB total)
    - Inline images with CID references
    - Comprehensive error handling and logging
    - Delivery metrics tracking
    - Configuration set support for analytics
    - Email validation and sanitization
    """

    # AWS SES limits
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024
    MAX_RECIPIENTS = 50
    MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024

    # Unsupported attachment types by SES
    BLOCKED_EXTENSIONS = {
        ".ade", ".adp", ".app", ".asp", ".bas", ".bat", ".cer", ".chm", ".cmd",
        ".com", ".cpl", ".crt", ".csh", ".der", ".exe", ".fxp", ".gadget", ".hlp",
        ".hta", ".inf", ".ins", ".isp", ".its", ".js", ".jse", ".ksh", ".lnk",
        ".mad", ".maf", ".mag", ".mam", ".maq", ".mar", ".mas", ".mat", ".mau",
        ".mav", ".maw", ".mda", ".mdb", ".mde", ".mdt", ".mdw", ".mdz", ".msc",
        ".msh", ".msh1", ".msh2", ".mshxml", ".msh1xml", ".msh2xml", ".msi",
        ".msp", ".mst", ".ops", ".pcd", ".pif", ".plg", ".prf", ".prg", ".pst",
        ".reg", ".scf", ".scr", ".sct", ".shb", ".shs", ".ps1", ".ps1xml",
        ".ps2", ".ps2xml", ".psc1", ".psc2", ".tmp", ".url", ".vb", ".vbe",
        ".vbs", ".vsmacros", ".vss", ".vst", ".vsw", ".ws", ".wsc", ".wsf", ".wsh"
    }

    def __init__(
        self, region_name: Optional[str] = None, configuration_set: Optional[str] = None,
        template_dir: Optional[str] = None,
    ):
        """
        Initialize SES Email Service

        Args:
            region_name: AWS region (defaults to settings)
            configuration_set: SES configuration set for tracking
            template_dir: Directory for email templates
        """
        self.region_name = region_name or settings.aws_region
        self.configuration_set = configuration_set
        self.default_sender = settings.email_from

        # Initialize SES client
        try:
            self.client = boto3.client(
                "ses", region_name=self.region_name,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            logger.info(
                "SES client initialized", region=self.region_name,
                configuration_set=configuration_set
            )
        except Exception as e:
            logger.error("Failed to initialize SES client", error=str(e))
            raise

        # Initialize Jinja2 environment for templates
        self._setup_template_environment(template_dir)

    def _setup_template_environment(self, template_dir: Optional[str]) -> None:
        """
        Set up Jinja2 template environment with security settings

        Args:
            template_dir: Custom template directory path
        """
        try:
            if template_dir:
                # Use FileSystemLoader for custom directory
                loader = FileSystemLoader(template_dir)
            else:
                # Use PackageLoader for templates within package
                loader = PackageLoader("src", "templates/email")

            self.jinja_env = Environment(
                loader=loader,
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
                enable_async=False
            )

            # Add custom filters
            self.jinja_env.filters["currency"] = self._format_currency
            self.jinja_env.filters["datetime"] = self._format_datetime

            logger.info("Jinja2 template environment initialized")

        except Exception as e:
            logger.warning(
                "Failed to setup template environment, templates disabled",
                error=str(e),
            )
            self.jinja_env = None

    @staticmethod
    def _format_currency(value: Union[int, float], currency: str = "INR") -> str:
        """Format currency for templates"""
        symbols = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}
        symbol = symbols.get(currency, currency)
        return f"{symbol}{value:,.2f}"
    
    @staticmethod
    def _format_datetime(value: Any, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime for templates"""
        from datetime import datetime
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value.strftime(format)
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    def _validate_recipients(
        self, to_addresses: List[str], cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None
    ) -> None:
        """
        Validate recipient email addresses

        Args:
            to_addresses: List of To recipients
            cc_addresses: List of CC recipients
            bcc_addresses: List of BCC recipients

        Raises:
            ValueError: If validation fails
        """
        all_recipients = (
            to_addresses
            + (cc_addresses or [])
            + (bcc_addresses or [])
        )

        if not all_recipients:
            raise ValueError("At least one recipient is required")
        
        if len(all_recipients) > self.MAX_RECIPIENTS:
            raise ValueError(
                f"Too many recipients. Maximum {self.MAX_RECIPIENTS} allowed."
            )
        
        for email in all_recipients:
            if not self._validate_email(email):
                raise ValueError(f"Invalid email address: {email}")
            
    def _validate_attachment(self, attachment: EmailAttachment) -> None:
        """
        Validate attachment

        Args:
            attachment: EmailAttachment object

        Raises:
            ValueError: If validation fails
        """
        # Check file extension
        file_ext = Path(attachment.filename).suffix.lower()
        if file_ext in self.BLOCKED_EXTENSIONS:
            raise ValueError(
                f"Attachment type not allowed: {file_ext}. "
                f"File: {attachment.filename}"
            )
        
        # Check file size
        content_size = len(attachment.content)
        if content_size > self.MAX_ATTACHMENT_SIZE:
            size_mb = content_size / (1024 * 1024)
            raise ValueError(
                f"Attachment too large: {size_mb:.2f}MB. "
                f"Maximum {self.MAX_ATTACHMENT_SIZE / (1024 * 1024)}MB allowed. "
                f"File: {attachment.filename}"
            )
        
    def render_template(
        self, template_name: str, context: Dict[str, Any],
        template_type: str = "html"
    ) -> str:
        """
        Render email template with context

        Args:
            template_name: Template filename (without extension)
            context: Template variables
            template_type: 'html' or 'text'

        Returns:
            Rendered template string

        Raises:
            ValueError: If template environment is not initialized
            TemplateNotFound: If template file is not found
        """
        if not self.jinja_env:
            raise ValueError("Template environment not initialized")
        
        try:
            template_file = f"{template_name}.{template_type}"
            template = self.jinja_env.get_template(template_file)
            rendered = template.render(**context)

            logger.debug(
                "Template rendered", template=template_name,
                type=template_type
            )

            return rendered
        except TemplateNotFound as e:
            logger.error("Template not found", template=template_name, error=str(e))
            raise
        except Exception as e:
            logger.error("Template rendering failed", template=template_name, error=str(e))
            raise

    def _build_mime_message(
        self, sender: str, to_addresses: List[str], subject: str,
        html_body: Optional[str] = None, text_body: Optional[str] = None,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        reply_to: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> MIMEMultipart:
        """
        Build MIME multipart message

        Args:
            sender: From email address
            to_addresses: List of To recipients
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            cc_addresses: List of CC recipients
            bcc_addresses: List of BCC recipients
            attachments: List of EmailAttachment objects
            reply_to: Reply-To email address
            custom_headers: Custom email headers

        Returns:
            MIMEMultipart message object
        """
        # Create message container
        message = MIMEMultipart("mixed")
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = ", ".join(to_addresses)

        if cc_addresses:
            message["Cc"] = ", ".join(cc_addresses)

        if reply_to:
            message["Reply-To"] = reply_to

        # Add custom headers
        if custom_headers:
            for header_name, header_value in custom_headers.items():
                message[header_name] = header_value

        # Add configuration set header for tracking
        if self.configuration_set:
            message.add_header("X-SES-CONFIGURATION-SET", self.configuration_set)

        # Create alternative container for text and HTML
        msg_alternative = MIMEMultipart("alternative")
        message.attach(msg_alternative)

        # Add text body (fallback)
        if text_body:
            part_text = MIMEText(text_body, "plain", "utf-8")
            msg_alternative.attach(part_text)

        # Add HTML body
        if html_body:
            # If there are inline images, create related container
            if attachments and any(a.disposition == "inline" for a in attachments):
                msg_related = MIMEMultipart("related")
                msg_alternative.attach(msg_related)

                part_html = MIMEText(html_body, "html", "utf-8")
                msg_related.attach(part_html)

                # Add inline images
                for attachment in attachments:
                    if attachment.disposition == "inline":
                        self._attach_inline_image(msg_related, attachment)

            else:
                part_html = MIMEText(html_body, "html", "utf-8")
                msg_alternative.attach(part_html)

        # Add regular attachments
        if attachments:
            for attachment in attachments:
                if attachment.disposition == "attachment":
                    self._attach_file(message, attachment)

        return message
    
    def _attach_file(
        self, message: MIMEMultipart, attachment: EmailAttachment
    ) -> None:
        """
        Attach file to message

        Args:
            message: MIME message object
            attachment: EmailAttachment object
        """
        # Determine MIME type
        maintype, subtype = attachment.content_type.split("/", 1)

        if maintype == "application":
            part = MIMEApplication(attachment.content, _subtype=subtype)
        elif maintype == "image":
            part = MIMEImage(attachment.content, _subtype=subtype)
        elif maintype == "text":
            part = MIMEText(attachment.content.decode("utf-8"), _subtype=subtype)
        else:
            part = MIMEBase(maintype, subtype)
            part.set_payload(attachment.content)
            encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition", attachment.disposition, filename=attachment.filename
        )

        message.attach(part)

    def _attach_inline_image(
        self, message: MIMEMultipart, attachment: EmailAttachment
    ) -> None:
        """
        Attach inline image with Content-ID

        Args:
            message: MIME message object
            attachment: EmailAttachment object with content_id
        """
        maintype, subtype = attachment.content_type.split("/", 1)
        part = MIMEImage(attachment.content, _subtype=subtype)
        part.add_header("Content-ID", f"<{attachment.content_id}>")
        part.add_header(
            "Content-Disposition", "inline", filename=attachment.filename
        )
        message.attach(part)

    async def send_email(
        self, to_addresses: Union[str, List[str]], subject: str,
        html_body: Optional[str] = None, text_body: Optional[str] = None,
        sender: Optional[str] = None, cc_addresses: Optional[Union[str, List[str]]] = None,
        bcc_addresses: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        reply_to: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email via Amazon SES

        Args:
            to_addresses: Recipient email(s)
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (fallback)
            sender: From email address (defaults to settings)
            cc_addresses: CC recipient(s)
            bcc_addresses: BCC recipient(s)
            attachments: List of EmailAttachment objects
            reply_to: Reply-To email address
            custom_headers: Custom email headers

        Returns:
            Dictionary with MessageId and other response data

        Raises:
            ValueError: If validation fails
            ClientError: If SES API call fails
        """
        # Normalize recipients to lists
        to_addresses = [to_addresses] if isinstance(to_addresses, str) else to_addresses
        cc_addresses = (
            [cc_addresses] if isinstance(cc_addresses, str) else (cc_addresses or [])
        )
        bcc_addresses = (
            [bcc_addresses] if isinstance(bcc_addresses, str) else (bcc_addresses or [])
        )

        # Validate inputs
        self._validate_recipients(to_addresses, cc_addresses, bcc_addresses)

        if not html_body and not text_body:
            raise ValueError("Either html_body or text_body must be provided")
        
        # Validate attachments
        if attachments:
            total_size = sum(len(a.content) for a in attachments)
            if total_size > self.MAX_MESSAGE_SIZE:
                raise ValueError(
                    f"Total message size exceeds {self.MAX_MESSAGE_SIZE / (1024 * 1024)}MB limit."
                )
            
            for attachment in attachments:
                self._validate_attachment(attachment)

        sender = sender or self.default_sender

        try:
            # Build MIME message
            message = self._build_mime_message(
                sender=sender, to_addresses=to_addresses, subject=subject,
                html_body=html_body, text_body=text_body, cc_addresses=cc_addresses,
                bcc_addresses=bcc_addresses, attachments=attachments, reply_to=reply_to,
                custom_headers=custom_headers,
            )

            # Prepare destinations
            destinations = to_addresses + cc_addresses + bcc_addresses

            # Send email via SES
            response = self.client.send_raw_email(
                Source=sender,
                Destinations=destinations,
                RawMessage={"Data": message.as_string()},
            )

            logger.info(
                "Email sent successfully",
                message_id=response["MessageId"],
                to=to_addresses,
                subject=subject,
                has_attachments=bool(attachments),
                attachment_count=len(attachments) if attachments else 0,
            )

            return {
                "success": True,
                "message_id": response["MessageId"],
                "recipients": len(destinations),
            }
        
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            logger.error(
                "SES send_raw_email failed",
                error_code=error_code,
                to=to_addresses,
                subject=subject,
            )

            # Map common SES errors
            if error_code == "MessageRejected":
                raise ValueError(f"Email rejected: {error_message}")
            elif error_code == "MailFromDomainNotVerifiedException":
                raise ValueError("Sender email/domain not verified in SES")
            elif error_code == "ConfigurationSetDoesNotExist":
                raise ValueError(f"Configuration set not found: {self.configuration_set}")
            else:
                raise

        except BotoCoreError as e:
            logger.error("Boto3 error during email send", error=str(e))
            raise

        except Exception as e:
            logger.error("Unexpected error during email send", error=str(e))
            raise

    async def send_templated_email(
        self, to_addresses: Union[str, List[str]], template_name: str,
        context: Dict[str, Any], sender: Optional[str] = None,
        cc_addresses: Optional[Union[str, List[str]]] = None,
        bcc_addresses: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        reply_to: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email using Jinja2 templates

        Template files expected:
        - {template_name}.subject.txt - Email subject
        - {template_name}.html - HTML body
        - {template_name}.txt - Plain text body (optional)

        Args:
            to_addresses: Recipient email(s)
            template_name: Template name (without extension)
            context: Template variables
            sender: From email address
            cc_addresses: CC recipient(s)
            bcc_addresses: BCC recipient(s)
            attachments: List of EmailAttachment objects
            reply_to: Reply-To email address
            custom_headers: Custom email headers

        Returns:
            Dictionary with MessageId and other response data
        """
        # Render subject
        subject = self.render_template(template_name, context, "subject.txt").strip()

        # Render HTML body
        html_body = self.render_template(template_name, context, "html")

        # Render text body (optional)
        try:
            text_body = self.render_template(template_name, context, "txt")
        except TemplateNotFound:
            # Text body is optional
            text_body = None
            logger.debug("Text template not found, using HTML only", template=template_name)

        # Send email
        return await self.send_email(
            to_addresses=to_addresses,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            sender=sender,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            attachments=attachments,
            reply_to=reply_to,
            custom_headers=custom_headers
        )
    
    def get_send_quota(self) -> Dict[str, Any]:
        """
        Get SES sending quota information

        Returns:
            Dictionary with quota details
        """
        try:
            response = self.client.get_send_quota()
            return {
                "max_24_hour_send": response["Max24HourSend"],
                "max_send_rate": response["MaxSendRate"],
                "sent_last_24_hours": response["SentLast24Hours"],
                "remaining": response["Max24HourSend"] - response["SentLast24Hours"],
            }
        except ClientError as e:
            logger.error("Failed to get send quota", error=str(e))
            raise

    def get_send_statistics(self) -> List[Dict[str, Any]]:
        """
        Get SES sending statistics for last 14 days

        Returns:
            List of data points with sending statistics
        """
        try:
            response = self.client.get_send_statistics()
            return response.get("SendDataPoints", [])
        except ClientError as e:
            logger.error("Failed to get send statistics", error=str(e))
            raise

    def verify_email_identity(self, email: str) -> bool:
        """
        Send verification email to verify email address

        Args:
            email: Email address to verify

        Returns:
            True if verification email sent successfully
        """
        try:
            self.client.verify_email_identity(EmailAddress=email)
            logger.info("Verification email sent", email=email)
            return True
        except ClientError as e:
            logger.error("Failed to send verification email", email=email, error=str(e))
            raise


# Global service instance
email_service = SESEmailService()


async def get_email_service() -> SESEmailService:
    """Dependency for getting email service in FastAPI routes"""
    return email_service


