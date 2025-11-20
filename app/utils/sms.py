# app/utils/sms.py

from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SMSService:
    """Centralized AWS SNS SMS service with template support."""

    def __init__(self):
        self.client = boto3.client(
            'sns',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    async def send_sms(
        self, phone_number: str, message: str, sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS via AWS SNS.

        Args:
            phone_number (str): Recipient's phone number in E.164 format.
            message (str): The message content to send.
            sender_id (Optional[str]): Optional sender ID to display on the recipient's device.

        Returns:
            Dict with message ID and status.
        """
        try:
            # Validate phone number format
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"

            # Set message attributes
            message_attributes = {
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": settings.sns_sms_type
                }
            }

            if sender_id:
                message_attributes["AWS.SNS.SMS.SenderID"] = {
                    "DataType": "String",
                    "StringValue": sender_id
                }

            # Send SMS
            response = self.client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes=message_attributes
            )

            logger.info(
                "sms_sent", message_id=response["MessageId"], phone=phone_number
            )

            return {
                "message_id": response["MessageId"],
                "status": "sent"
            }
        
        except ClientError as e:
            logger.error(
                "sns_send_error", error=str(e), error_code=e.response["Error"]["Code"]
            )
            raise
        except Exception as e:
            logger.error("sms_send_error", error=str(e))
            raise

    async def send_templated_sms(
        self, db: AsyncSession, phone_number: str, template_name: str,
        variables: Dict[str, str], sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS using a stored template.

        Args:
            db (AsyncSession): Database session to fetch the template.
            phone_number (str): Recipient's phone number in E.164 format.
            template_name (str): Name of the SMS template.
            variables (Dict[str, str]): Variables to replace in the template.
            sender_id (Optional[str]): Optional sender ID to display on the recipient's device.

        Returns:
            Dict with message ID and status.
        """
        from app.modules.users.models import SMSTemplate

        # Fetch template from database
        stmt = select(SMSTemplate).where(
            SMSTemplate.name == template_name,
            SMSTemplate.is_active == True
        )
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            raise ValueError(f"SMS template '{template_name}' not found or inactive.")
        
        # Replace variables in templates
        message = template.content
        for key, value in variables.items():
            message = message.replace(f"{{{{ {key} }}}}", value)

        return await self.send_sms(
            phone_number=phone_number,
            message=message,
            sender_id=sender_id
        )
    

sms_service = SMSService()
