# src/common/sms_helpers.py

"""
SMS Helper Functions for Common Restaurant Fleet Platform Scenarios
Provides convenient methods for OTP, order notifications, and delivery updates
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.common.sms_service import SMSType, sms_service, SNSSMSService
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class SMSHelpers:
    """
    High-level SMS helper functions for common scenarios
    """

    def __init__(self, service: Optional[SNSSMSService] = None):
        """
        Initialize SMS helpers

        Args:
            service: SNSSMSService instance (uses global if not provided)
        """
        self.service = service or sms_service
        self.company_name = settings.app_name

    async def send_verification_otp(
        self,
        phone_number: str,
        purpose: str = "registration",
        length: int = 6,
        validity_minutes: int = 10,
    ) -> Dict[str, Any]:
        """
        Send verification OTP for user registration/login

        Args:
            phone_number: User's phone number
            purpose: OTP purpose (registration, login, password_reset, etc.)
            length: OTP length
            validity_minutes: OTP validity in minutes

        Returns:
            Send result dictionary
        """
        try:
            result = await self.service.send_otp(
                phone_number=phone_number,
                length=length,
                validity_minutes=validity_minutes,
                purpose=purpose,
            )

            logger.info(
                "Verification OTP sent",
                phone_number=phone_number[:5] + "***",
                purpose=purpose,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send verification OTP",
                phone_number=phone_number[:5] + "***",
                purpose=purpose,
                error=str(e),
            )
            raise

    async def verify_user_otp(
        self,
        phone_number: str,
        otp: str,
        purpose: str = "registration",
    ) -> bool:
        """
        Verify user-provided OTP

        Args:
            phone_number: User's phone number
            otp: OTP provided by user
            purpose: OTP purpose (must match send_verification_otp)

        Returns:
            True if OTP is valid, False otherwise
        """
        try:
            is_valid = await self.service.verify_otp(
                phone_number=phone_number,
                otp=otp,
                purpose=purpose,
            )

            if is_valid:
                logger.info(
                    "OTP verified successfully",
                    phone_number=phone_number[:5] + "***",
                    purpose=purpose,
                )
            else:
                logger.warning(
                    "OTP verification failed",
                    phone_number=phone_number[:5] + "***",
                    purpose=purpose,
                )

            return is_valid

        except Exception as e:
            logger.error(
                "OTP verification error",
                phone_number=phone_number[:5] + "***",
                error=str(e),
            )
            return False

    async def send_order_confirmation(
        self,
        phone_number: str,
        order_number: str,
        restaurant_name: str,
        estimated_time: str,
        track_url: str,
    ) -> Dict[str, Any]:
        """
        Send order confirmation SMS

        Args:
            phone_number: Customer's phone number
            order_number: Order number
            restaurant_name: Restaurant name
            estimated_time: Estimated delivery time
            track_url: Order tracking URL

        Returns:
            Send result dictionary
        """
        message = (
            f"Order {order_number} confirmed at {restaurant_name}! "
            f"Estimated delivery: {estimated_time}. "
            f"Track: {track_url}"
        )

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Order confirmation SMS sent",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send order confirmation SMS",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_order_status_update(
        self,
        phone_number: str,
        order_number: str,
        status: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send order status update SMS

        Args:
            phone_number: Customer's phone number
            order_number: Order number
            status: New order status
            message: Status update message

        Returns:
            Send result dictionary
        """
        sms_message = f"Order {order_number} - {status}: {message}"

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=sms_message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Order status update SMS sent",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                status=status,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send order status update SMS",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_delivery_assignment(
        self,
        phone_number: str,
        order_number: str,
        driver_name: str,
        driver_phone: str,
        estimated_time: str,
    ) -> Dict[str, Any]:
        """
        Send delivery assignment notification

        Args:
            phone_number: Customer's phone number
            order_number: Order number
            driver_name: Delivery driver name
            driver_phone: Driver's contact number
            estimated_time: Estimated delivery time

        Returns:
            Send result dictionary
        """
        message = (
            f"Your order {order_number} is out for delivery! "
            f"Driver: {driver_name} ({driver_phone}). "
            f"ETA: {estimated_time}"
        )

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Delivery assignment SMS sent",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send delivery assignment SMS",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_delivery_completed(
        self,
        phone_number: str,
        order_number: str,
        feedback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send delivery completion notification

        Args:
            phone_number: Customer's phone number
            order_number: Order number
            feedback_url: Feedback/rating URL (optional)

        Returns:
            Send result dictionary
        """
        message = f"Your order {order_number} has been delivered. Enjoy your meal!"
        
        if feedback_url:
            message += f" Rate us: {feedback_url}"

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Delivery completed SMS sent",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send delivery completed SMS",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_payment_confirmation(
        self,
        phone_number: str,
        order_number: str,
        amount: float,
        payment_method: str,
    ) -> Dict[str, Any]:
        """
        Send payment confirmation SMS

        Args:
            phone_number: Customer's phone number
            order_number: Order number
            amount: Payment amount
            payment_method: Payment method used

        Returns:
            Send result dictionary
        """
        message = (
            f"Payment of ₹{amount:.2f} received for order {order_number} "
            f"via {payment_method}. Thank you!"
        )

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Payment confirmation SMS sent",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send payment confirmation SMS",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_driver_assignment_notification(
        self,
        phone_number: str,
        order_number: str,
        pickup_address: str,
        delivery_address: str,
        customer_phone: str,
    ) -> Dict[str, Any]:
        """
        Send order assignment notification to driver

        Args:
            phone_number: Driver's phone number
            order_number: Order number
            pickup_address: Restaurant pickup address
            delivery_address: Customer delivery address
            customer_phone: Customer's contact number

        Returns:
            Send result dictionary
        """
        message = (
            f"New delivery: Order {order_number}. "
            f"Pickup: {pickup_address}. "
            f"Deliver to: {delivery_address}. "
            f"Customer: {customer_phone}"
        )

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Driver assignment SMS sent",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send driver assignment SMS",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_restaurant_new_order_alert(
        self,
        phone_number: str,
        order_number: str,
        items_count: int,
        total_amount: float,
        customer_name: str,
    ) -> Dict[str, Any]:
        """
        Send new order alert to restaurant

        Args:
            phone_number: Restaurant owner's phone number
            order_number: Order number
            items_count: Number of items in order
            total_amount: Total order amount
            customer_name: Customer name

        Returns:
            Send result dictionary
        """
        message = (
            f"New order {order_number} from {customer_name}! "
            f"{items_count} items, ₹{total_amount:.2f}. "
            f"Please confirm."
        )

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Restaurant new order alert SMS sent",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send restaurant new order alert SMS",
                phone_number=phone_number[:5] + "***",
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_promotional_message(
        self,
        phone_numbers: List[str],
        offer_title: str,
        offer_details: str,
        promo_code: Optional[str] = None,
        valid_until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send promotional SMS to multiple customers

        Args:
            phone_numbers: List of customer phone numbers
            offer_title: Offer title
            offer_details: Offer details
            promo_code: Promo code (optional)
            valid_until: Offer validity date (optional)

        Returns:
            List of send results
        """
        message = f"{offer_title}: {offer_details}"
        
        if promo_code:
            message += f" Use code: {promo_code}"
        
        if valid_until:
            message += f" Valid till {valid_until.strftime('%d %b')}"

        try:
            results = await self.service.send_bulk_sms(
                phone_numbers=phone_numbers,
                message=message,
                sms_type=SMSType.PROMOTIONAL,
            )

            successful = sum(1 for r in results if r.get("success"))
            logger.info(
                "Promotional SMS campaign completed",
                total=len(phone_numbers),
                successful=successful,
                failed=len(phone_numbers) - successful,
            )

            return results

        except Exception as e:
            logger.error(
                "Promotional SMS campaign failed",
                total=len(phone_numbers),
                error=str(e),
            )
            raise

    async def send_table_booking_reminder(
        self,
        phone_number: str,
        restaurant_name: str,
        booking_time: datetime,
        table_number: Optional[str] = None,
        contact_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send table booking reminder

        Args:
            phone_number: Customer's phone number
            restaurant_name: Restaurant name
            booking_time: Booking time
            table_number: Table number (optional)
            contact_number: Restaurant contact (optional)

        Returns:
            Send result dictionary
        """
        time_str = booking_time.strftime("%I:%M %p")
        date_str = booking_time.strftime("%d %b")
        
        message = f"Reminder: Your table at {restaurant_name} is booked for {time_str}, {date_str}"
        
        if table_number:
            message += f". Table: {table_number}"
        
        if contact_number:
            message += f". Contact: {contact_number}"

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Table booking reminder SMS sent",
                phone_number=phone_number[:5] + "***",
                restaurant_name=restaurant_name,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send table booking reminder SMS",
                phone_number=phone_number[:5] + "***",
                restaurant_name=restaurant_name,
                error=str(e),
            )
            raise

    async def send_password_reset_otp(
        self,
        phone_number: str,
        length: int = 6,
        validity_minutes: int = 15,
    ) -> Dict[str, Any]:
        """
        Send password reset OTP

        Args:
            phone_number: User's phone number
            length: OTP length
            validity_minutes: OTP validity in minutes

        Returns:
            Send result dictionary
        """
        return await self.send_verification_otp(
            phone_number=phone_number,
            purpose="password_reset",
            length=length,
            validity_minutes=validity_minutes,
        )

    async def send_account_alert(
        self,
        phone_number: str,
        alert_type: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send account security/activity alert

        Args:
            phone_number: User's phone number
            alert_type: Alert type (login, password_change, etc.)
            message: Alert message

        Returns:
            Send result dictionary
        """
        sms_message = f"Security Alert ({alert_type}): {message}"

        try:
            result = await self.service.send_sms(
                phone_number=phone_number,
                message=sms_message,
                sms_type=SMSType.TRANSACTIONAL,
            )

            logger.info(
                "Account alert SMS sent",
                phone_number=phone_number[:5] + "***",
                alert_type=alert_type,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send account alert SMS",
                phone_number=phone_number[:5] + "***",
                alert_type=alert_type,
                error=str(e),
            )
            raise


# Global helper instance
sms_helpers = SMSHelpers()


async def get_sms_helpers() -> SMSHelpers:
    """Dependency for getting SMS helpers in FastAPI routes"""
    return sms_helpers