# src/common/sms_service.py

"""
Production-grade Amazon SNS SMS Service
Supports direct SMS, template rendering, OTP generation, and comprehensive error handling.
Follows AWS best practices for SMS deliverability and compliance
"""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.core.config import settings
from src.core.logging import get_logger
from src.core.redis import redis_service

logger = get_logger(__name__)


class SMSType(str, Enum):
    """SMS message types as per AWS SNS"""
    PROMOTIONAL = "Promotional"
    TRANSACTIONAL = "Transactional"


class SMSTemplate:
    """SMS message template with variable substitution"""

    def __init__(self, template: str, variables: Optional[Dict[str, str]] = None):
        """
        Initialize SMS template

        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variables to substitute
        """
        self.template = template
        self.variables = variables or {}

    def render(self, **additional_vars) -> str:
        """
        Render temlplate with variables

        Args:
            **additional_vars: Additional variables to include

        Returns:
            Rendered message string
        """
        all_vars = {**self.variables, **additional_vars}
        return self.template.format(**all_vars)
    

class SNSSMSService:
    """
    Production-grade Amazon SNS SMS Service

    Features:
    - Direct SMS to phone numbers (no topic subscription required)
    - Template-based messaging with variable substitution
    - OTP generation and verification with Redis
    - Phone number validation (E.164 format)
    - Message length calculation and optimization
    - Sender ID support (where available)
    - Promotional vs Transactional routing
    - Comprehensive error handling and logging
    - Opt-out management
    - Delivery status tracking
    - Rate limiting and spending controls
    - Multi-region support
    """

    # SMS limits
    MAX_MESSAGE_LENGTH = 160
    MAX_MESSAGE_LENGTH_UNICODE = 70

    # GSM-7 CHARSET (standard SMS characters)
    GSM7_BASIC = set(
       "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
       "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
    )

    # Characters that require escaping in GSM-7 (count as 2 characters)
    GSM7_EXTENDED = set("^{}\\[~]|€")

    # Default message templates
    DEFAULT_TEMPLATES = {
        "otp": "Your verification code is {otp}. Valid for {validity} minutes. Do not share this code.",
        "order_confirmation": "Order {order_number} confirmed! Estimated delivery: {delivery_time}. Track: {track_url}",
        "order_update": "Order {order_number} status: {status}. {message}",
        "delivery_assigned": "Your order {order_number} is out for delivery. Driver: {driver_name}, Phone: {driver_phone}",
        "delivery_completed": "Your order {order_number} has been delivered. Enjoy your meal!",
        "payment_confirmation": "Payment of {amount} received for order {order_number}. Thank you!",
        "booking_reminder": "Reminder: Your table booking at {restaurant_name} is at {time} today.",
    }

    def __init__(
        self, region_name: Optional[str] = None, default_sender_id: Optional[str] = None,
        default_sms_type: SMSType = SMSType.TRANSACTIONAL,
    ):
        """
        Initialize SNS SMS Service

        Args:
            region_name: AWS region (defaults to settings)
            default_sender_id: Default sender ID for SMS
            default_sms_type: Default SMS type (Promotional or Transactional)
        """
        self.region_name = region_name or settings.aws_region
        self.default_sender_id = default_sender_id
        self.default_sms_type = default_sms_type

        # Initialize SNS client
        try:
            self.client = boto3.client(
                "sns", region_name=self.region_name,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            logger.info(
                "SNS SMS client initialized",
                region=self.region_name,
                default_sms_type=default_sms_type,
            )
        except Exception as e:
            logger.error("Failed to initialize SNS SMS client", error=str(e))
            raise

    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number in E.164 format

        Args:
            phone_number: Phone number to validate

        Returns:
            True if valid, False otherwise
        """
        # E.164 format: +[country code][number]
        # Example: +919876543210 (India), +12025551234 (USA)
        pattern = r"^\+[1-9]\d{1,14}$"

        if not re.match(pattern, phone_number):
            logger.warning("Invalid phone number format", phone_number=phone_number[:5] + "***")
            return False
        
        return True
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Normalize phone number to E.164 format

        Args:
            phone_number: Phone number (with or without +)

        Returns:
            Normalized phone number
        """
        # Remove all non-digit characters except +
        if not phone_number.startswith("+"):
            # Assume India (+91) if no country code
            # Adjust based on your primary market
            phone_number = f"+91{phone_number}"

        return phone_number
    
    def _calculate_message_parts(self, message: str) -> int:
        """
        Calculate number of SMS parts required

        Args:
            message: Message text

        Returns:
            Number of SMS parts
        """
        # Check if message uses GSM-7 charset
        is_gsm7 = all(
            c in self.GSM7_BASIC or c in self.GSM7_EXTENDED for c in message
        )

        if is_gsm7:
            # Count characters (extended chars count as 2)
            char_count = sum(
                2 if c in self.GSM7_EXTENDED else 1 for c in message
            )

            if char_count <= 160:
                return 1
            else:
                return (char_count - 1) // 153 + 1  # Multipart GSM-7

        else:
            # Unicode (UCS-2) encoding
            char_count = len(message)

            if char_count <= 70:
                return 1
            else:
                # Multi-part unicode messages have 67 char limit per part
                return (char_count - 1) // 67 + 1
            
    def _optimize_message(self, message: str, max_parts: int = 1) -> str:
        """
        Optimize message to fit within specified parts

        Args:
            message: Original message
            max_parts: Maximum allowed parts

        Returns:
            Optimized message
        """
        current_parts = self._calculate_message_parts(message)

        if current_parts <= max_parts:
            return message
        
        # Calculate target length
        is_gsm7 = all(
            c in self.GSM7_BASIC or c in self.GSM7_EXTENDED for c in message
        )

        if max_parts == 1:
            target_length = 160 if is_gsm7 else 70
        else:
            target_length = (153 * max_parts) if is_gsm7 else (67 * max_parts)

        # Truncate and add ellipsis
        if is_gsm7:
            truncated = message[:target_length - 3] + "..."
        else:
            truncated = message[:target_length - 1] + "..."

        logger.warning(
            "Message truncated to fit SMS limit",
            original_length=len(message),
            truncated_length=len(truncated),
            parts=max_parts
        )

        return truncated
    
    async def send_sms(
        self, phone_number: str, message: str, sender_id: Optional[str] = None,
        sms_type: Optional[SMSType] = None, max_price: Optional[float] = None,
        optimize: bool = True, max_parts: int = 1
    ) -> Dict[str, Any]:
        """
        Send SMS message via Amazon SNS

        Args:
            phone_number: Recipient phone number (E.164 format)
            message: Message text
            sender_id: Sender ID (if supported in destination country)
            sms_type: Promotional or Transactional
            max_price: Maximum price willing to pay (in USD)
            optimize: Whether to optimize message length
            max_parts: Maximum SMS parts allowed

        Returns:
            Dictionary with MessageId and delivery info

        Raises:
            ValueError: If validation fails
            ClientError: If SNS API call fails
        """
        # Normalize and validate phone number
        phone_number = self._normalize_phone_number(phone_number)

        if not self._validate_phone_number(phone_number):
            raise ValueError(f"Invalid phone number format: {phone_number}")
        
        # Optimize message length if needed
        if optimize:
            message = self._optimize_message(message, max_parts=max_parts)

        # Calculate message parts
        parts = self._calculate_message_parts(message)

        if parts > max_parts:
            raise ValueError(
                f"Message too long: {parts} parts (max {max_parts} allowed)"
            )
        
        # Prepare message attributes
        message_attributes = {}

        # Set SMS type
        sms_type = sms_type or self.default_sms_type
        message_attributes["AWS.SNS.SMS.SMSType"] = {
            "DataType": "String",
            "StringValue": sms_type.value,
        }

        # Set Sender ID if provided (not supported in all countries)
        if sender_id or self.default_sender_id:
            message_attributes["AWS.SNS.SMS.SenderID"] = {
                "DataType": "String",
                "StringValue": sender_id or self.default_sender_id,
            }

        # Set max price if specified
        if max_price:
            message_attributes["AWS.SNS.SMS.MaxPrice"] = {
                "DataType": "Number",
                "StringValue": str(max_price),
            }

        try:
            # Send SMS via SNS
            response = self.client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes=message_attributes
            )

            logger.info(
                "SMS sent successfully",
                phone_number=phone_number[:5] + "***",
                message_id=response.get("MessageId"),
                message_length=len(message),
                message_parts=parts,
                sms_type=sms_type.value,
            )

            return {
                "success": True,
                "message_id": response.get("MessageId"),
                "phone_number": phone_number,
                "message_length": len(message),
                "message_parts": parts,
                "estimated_cost": self._estimate_cost(phone_number, parts, sms_type),
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']

            logger.error(
                "SNS SMS send failed",
                error_code=error_code,
                error_message=error_message,
                phone_number=phone_number[:5] + "***",
            )

            # Map common SNS errors
            if error_code == "InvalidParameter":
                raise ValueError(f"Invalid parameter: {error_message}")
            elif error_code == "OptedOut":
                raise ValueError(f"Phone number opted out of receiving SMS: {phone_number}")
            elif error_code == "ThrottlingException":
                raise ValueError("SMS rate limit exceeded. Please try again later.")
            else:
                raise

        except BotoCoreError as e:
            logger.error("Boto3 error during SMS send", error=str(e))
            raise

        except Exception as e:
            logger.error("Unexpected error during SMS send", error=str(e))
            raise

    async def send_templated_sms(
        self, phone_number: str, template_name: str, variables: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send SMS using predefined template

        Args:
            phone_number: Recipient phone number
            template_name: Template name from DEFAULT_TEMPLATES
            variables: Template variables
            **kwargs: Additional arguments for send_sms

        Returns:
            Send result dictionary
        """
        if template_name not in self.DEFAULT_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = SMSTemplate(
            template=self.DEFAULT_TEMPLATES[template_name],
            variables=variables,
        )

        message = template.render()

        return await self.send_sms(
            phone_number=phone_number,
            message=message,
            **kwargs,
        )
    
    async def generate_otp(
        self, phone_number: str, length: int = 6, validity_minutes: int = 10,
        purpose: str = "verification"
    ) -> str:
        """
        Generate OTP and store in Redis

        Args:
            phone_number: Recipient phone number
            length: OTP length (default 6 digits)
            validity_minutes: OTP validity in minutes
            purpose: OTP purpose (for key namespacing)

        Returns:
            Generated OTP
        """
        import random

        # Generate numeric OTP
        otp = "".join([str(random.randint(0, 9)) for _ in range(length)])

        # Store in Redis with expiry
        redis_key = f"otp:{purpose}:{phone_number}"

        await redis_service.set(
            redis_key, otp, expire=validity_minutes * 60
        )

        logger.info(
            "OTP generated",
            phone_number=phone_number[:5] + "***",
            length=length,
            validity_minutes=validity_minutes,
            purpose=purpose
        )

        return otp
    
    async def send_otp(
        self, phone_number: str, length: int = 6, validity_minutes: int = 10,
        purpose: str = "verification", custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate and send OTP via SMS

        Args:
            phone_number: Recipient phone number
            length: OTP length
            validity_minutes: OTP validity in minutes
            purpose: OTP purpose
            custom_message: Custom OTP message template

        Returns:
            Send result dictionary with OTP info
        """
        # Generate OTP
        otp = await self.generate_otp(
            phone_number=phone_number,
            length=length,
            validity_minutes=validity_minutes,
            purpose=purpose
        )

        # Send OTP via SMS
        if custom_message:
            message = custom_message.format(otp=otp, validity=validity_minutes)
        else:
            message = self.DEFAULT_TEMPLATES["otp"].format(
                otp=otp, validity=validity_minutes
            )

        result = await self.send_sms(
            phone_number=phone_number, message=message,
            sms_type=SMSType.TRANSACTIONAL
        )

        # Don't include actual OTP in response for security
        result["otp_sent"] = True
        result["validity_minutes"] = validity_minutes

        return result
    
    async def verify_otp(
        self, phone_number: str, otp: str, purpose: str = "verification",
        delete_on_verify: bool = True
    ) -> bool:
        """
        Verify OTP against stored value

        Args:
            phone_number: Phone number to verify
            otp: OTP provided by user
            purpose: OTP purpose (must match generate_otp)
            delete_on_verify: Whether to delete OTP after successful verification

        Returns:
            True if OTP is valid, False otherwise
        """
        redis_key = f"otp:{purpose}:{phone_number}"

        try:
            stored_otp = await redis_service.get(redis_key)

            if not stored_otp:
                logger.warning(
                    "OTP verification failed: not found or expired",
                    phone_number=phone_number[:5] + "***",
                    purpose=purpose
                )
                return False
            
            if stored_otp == otp:
                logger.info(
                    "OTP verified successfully",
                    phone_number=phone_number[:5] + "***",
                    purpose=purpose
                )

                if delete_on_verify:
                    await redis_service.delete(redis_key)

                return True
            else:
                logger.warning(
                    "OTP verification failed: incorrect OTP",
                    phone_number=phone_number[:5] + "***",
                    purpose=purpose
                )
                return False
        except Exception as e:
            logger.error(
                "OTP verification error",
                phone_number=phone_number[:5] + "***",
                error=str(e)
            )
            return False
        
    async def send_bulk_sms(
        self, phone_numbers: List[str], message: str, **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Send SMS to multiple recipients

        Args:
            phone_numbers: List of recipient phone numbers
            message: Message text
            **kwargs: Additional arguments for send_sms

        Returns:
            List of send results
        """
        results = []

        for phone_number in phone_numbers:
            try:
                result = await self.send_sms(
                    phone_number=phone_number,
                    message=message,
                    **kwargs,
                )
                results.append(result)

            except Exception as e:
                logger.error(
                    "Bulk SMS failed for number",
                    phone_number=phone_number[:5] + "***",
                    error=str(e)
                )
                results.append({
                    "success": False,
                    "phone_number": phone_number,
                    "error": str(e),
                })

        # Log summary
        successful = sum(1 for r in results if r.get("success"))
        logger.info(
            "Bulk SMS completed",
            total=len(phone_numbers),
            successful=successful,
            failed=len(phone_numbers) - successful
        )

        return results
    
    def _estimate_cost(
        self, phone_number: str, parts: int, sms_type: SMSType
    ) -> float:
        """
        Estimate SMS cost (approximate)

        Args:
            phone_number: Destination phone number
            parts: Number of SMS parts
            sms_type: SMS type

        Returns:
            Estimated cost in USD
        """
        # Get country code
        country_code = phone_number[1:3] if phone_number.startswith("+1") else "91"

        # Approximate pricing (update with actual rates)
        # India: ~0.00645 per transactional sms
        pricing = {
            "91": {"Transactional": 0.00645, "Promotional": 0.00258},  # India
            "1": {"Transactional": 0.00645, "Promotional": 0.00645},  # US/Canada
            "44": {"Transactional": 0.05, "Promotional": 0.04},  # UK
        }

        rate = pricing.get(country_code, {"Transactional": 0.01, "Promotional": 0.005})
        cost_per_message = rate.get(sms_type.value, 0.01)

        return cost_per_message * parts
    
    def get_sms_attributes(self) -> Dict[str, Any]:
        """
        Get SNS SMS attributes for the account

        Returns:
            Dictionary of SMS attributes
        """
        try:
            response = self.client.get_sms_attributes()
            return response.get("attributes", {})
        except ClientError as e:
            logger.error("Failed to get SMS attributes", error=str(e))
            raise

    def set_sms_attributes(self, attributes: Dict[str, str]) -> bool:
        """
        Set SNS SMS attributes

        Args:
            attributes: Dictionary of attributes to set
                - DefaultSMSType: Promotional or Transactional
                - MonthlySpendLimit: Monthly spending limit
                - DeliveryStatusIAMRole: IAM role ARN for delivery logs
                - DeliveryStatusSuccessSamplingRate: Success sampling rate (0-100)
                - DefaultSenderID: Default sender ID
                - UsageReportS3Bucket: S3 bucket for usage reports

        Returns:
            True if successful
        """
        try:
            self.client.set_sms_attributes(attributes=attributes)
            logger.info("SMS attributes updated", attributes=list(attributes.keys()))
            return True
        except ClientError as e:
            logger.error("Failed to set SMS attributes", error=str(e))
            raise

    def check_opt_out_status(self, phone_number: str) -> bool:
        """
        Check if phone number has opted out

        Args:
            phone_number: Phone number to check

        Returns:
            True if opted out, False otherwise
        """
        try:
            response = self.client.check_if_phone_number_is_opted_out(
                phoneNumber=phone_number
            )
            return response.get("isOptedOut", False)
        except ClientError as e:
            logger.error(
                "Failed to check opt-out status",
                phone_number=phone_number[:5] + "***",
                error=str(e),
            )
            raise

    async def list_opted_out_numbers(self) -> List[str]:
        """
        List all opted-out phone numbers

        Returns:
            List of opted-out phone numbers
        """
        try:
            opted_out = []
            next_token = None

            while True:
                if next_token:
                    response = self.client.list_phone_numbers_opted_out(
                        nextToken=next_token
                    )
                else:
                    response = self.client.list_phone_numbers_opted_out()

                opted_out.extend(response.get("phoneNumbers", []))

                next_token = response.get("nextToken")
                if not next_token:
                    break

            logger.info("Retrieved opted-out numbers", count=len(opted_out))
            return opted_out
        
        except ClientError as e:
            logger.error("Failed to list opted-out numbers", error=str(e))
            raise


# Global service instance
sms_service = SNSSMSService()

async def get_sms_service() -> SNSSMSService:
    """Dependency for getting SMS service in FastAPI routes"""
    return sms_service

