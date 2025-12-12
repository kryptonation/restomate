# src/common/email_helpers.py

"""
Email Helper Functions and Pre-configured Templates
Provides convenient methods for common email scenarios in the restaurant fleet platform
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.common.email_service import EmailAttachment, SESEmailService, email_service
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class EmailHelpers:
    """
    High-level email helper functions for common email scenarios
    """

    def __init__(self, service: Optional[SESEmailService] = None):
        """
        Initialize email helpers

        Args:
            service: SESEmailService instance (uses global if not provided)
        """
        self.service = service or email_service
        self.company_name = settings.app_name
        self.support_email = settings.email_from
        self.current_year = datetime.now().year

    def _get_base_context(self, extra_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get base template context with common variables

        Args:
            extra_context: Additional context variables

        Returns:
            Dictionary with base context
        """
        context = {
            "company_name": self.company_name,
            "current_year": self.current_year,
            "support_email": self.support_email,
            "support_url": f"https://yourapp.com/support",
            "privacy_url": f"https://yourapp.com/privacy",
            "terms_url": f"https://yourapp.com/terms",
            "logo_url": f"https://yourapp.com/static/logo.png",
        }

        if extra_context:
            context.update(extra_context)

        return context

    async def send_welcome_email(
        self,
        user_email: str,
        user_name: str,
        user_role: str,
        verification_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send welcome email to new user

        Args:
            user_email: User's email address
            user_name: User's full name
            user_role: User's role (customer, restaurant_owner, delivery_partner, etc.)
            verification_url: Email verification URL (if applicable)

        Returns:
            Send result dictionary
        """
        context = self._get_base_context({
            "user_name": user_name,
            "user_role": user_role,
            "verification_url": verification_url,
            "dashboard_url": "https://yourapp.com/dashboard",
        })

        try:
            result = await self.service.send_templated_email(
                to_addresses=user_email,
                template_name="welcome",
                context=context,
            )

            logger.info(
                "Welcome email sent",
                user_email=user_email,
                user_role=user_role,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send welcome email",
                user_email=user_email,
                error=str(e),
            )
            raise

    async def send_order_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        order_id: UUID,
        order_number: str,
        order_items: List[Dict[str, Any]],
        order_total: float,
        delivery_address: str,
        estimated_delivery_time: str,
        restaurant_name: str,
        restaurant_phone: str,
    ) -> Dict[str, Any]:
        """
        Send order confirmation email

        Args:
            customer_email: Customer's email
            customer_name: Customer's name
            order_id: Order UUID
            order_number: Human-readable order number
            order_items: List of order items with name, quantity, price
            order_total: Total order amount
            delivery_address: Delivery address
            estimated_delivery_time: Estimated delivery time
            restaurant_name: Restaurant name
            restaurant_phone: Restaurant contact number

        Returns:
            Send result dictionary
        """
        context = self._get_base_context({
            "customer_name": customer_name,
            "order_id": str(order_id),
            "order_number": order_number,
            "order_items": order_items,
            "order_total": order_total,
            "delivery_address": delivery_address,
            "estimated_delivery_time": estimated_delivery_time,
            "restaurant_name": restaurant_name,
            "restaurant_phone": restaurant_phone,
            "track_order_url": f"https://yourapp.com/orders/{order_id}",
        })

        try:
            result = await self.service.send_templated_email(
                to_addresses=customer_email,
                template_name="order_confirmation",
                context=context,
            )

            logger.info(
                "Order confirmation email sent",
                customer_email=customer_email,
                order_id=order_id,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send order confirmation email",
                customer_email=customer_email,
                order_id=order_id,
                error=str(e),
            )
            raise

    async def send_order_status_update(
        self,
        customer_email: str,
        customer_name: str,
        order_number: str,
        old_status: str,
        new_status: str,
        status_message: str,
        estimated_time: Optional[str] = None,
        tracking_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send order status update email

        Args:
            customer_email: Customer's email
            customer_name: Customer's name
            order_number: Order number
            old_status: Previous order status
            new_status: New order status
            status_message: Status update message
            estimated_time: Updated estimated time
            tracking_url: Order tracking URL

        Returns:
            Send result dictionary
        """
        context = self._get_base_context({
            "customer_name": customer_name,
            "order_number": order_number,
            "old_status": old_status,
            "new_status": new_status,
            "status_message": status_message,
            "estimated_time": estimated_time,
            "tracking_url": tracking_url,
        })

        try:
            result = await self.service.send_templated_email(
                to_addresses=customer_email,
                template_name="order_status_update",
                context=context,
            )

            logger.info(
                "Order status update email sent",
                customer_email=customer_email,
                order_number=order_number,
                new_status=new_status,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send order status update email",
                customer_email=customer_email,
                order_number=order_number,
                error=str(e),
            )
            raise

    async def send_password_reset(
        self,
        user_email: str,
        user_name: str,
        reset_token: str,
        expires_at: datetime,
    ) -> Dict[str, Any]:
        """
        Send password reset email

        Args:
            user_email: User's email address
            user_name: User's name
            reset_token: Password reset token
            expires_at: Token expiration datetime

        Returns:
            Send result dictionary
        """
        reset_url = f"https://yourapp.com/reset-password?token={reset_token}"
        expires_in_minutes = int((expires_at - datetime.now()).total_seconds() / 60)

        context = self._get_base_context({
            "user_name": user_name,
            "reset_url": reset_url,
            "expires_in_minutes": expires_in_minutes,
        })

        try:
            result = await self.service.send_templated_email(
                to_addresses=user_email,
                template_name="password_reset",
                context=context,
            )

            logger.info(
                "Password reset email sent",
                user_email=user_email,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send password reset email",
                user_email=user_email,
                error=str(e),
            )
            raise

    async def send_invoice(
        self,
        customer_email: str,
        customer_name: str,
        invoice_number: str,
        invoice_date: datetime,
        invoice_amount: float,
        order_items: List[Dict[str, Any]],
        tax_amount: float,
        delivery_fee: float,
        discount_amount: float,
        pdf_attachment: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Send invoice email with optional PDF attachment

        Args:
            customer_email: Customer's email
            customer_name: Customer's name
            invoice_number: Invoice number
            invoice_date: Invoice date
            invoice_amount: Total invoice amount
            order_items: List of order items
            tax_amount: Tax amount
            delivery_fee: Delivery fee
            discount_amount: Discount amount
            pdf_attachment: PDF invoice as bytes (optional)

        Returns:
            Send result dictionary
        """
        context = self._get_base_context({
            "customer_name": customer_name,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date.strftime("%B %d, %Y"),
            "invoice_amount": invoice_amount,
            "order_items": order_items,
            "tax_amount": tax_amount,
            "delivery_fee": delivery_fee,
            "discount_amount": discount_amount,
            "subtotal": invoice_amount - tax_amount - delivery_fee + discount_amount,
        })

        attachments = []
        if pdf_attachment:
            attachments.append(
                EmailAttachment(
                    filename=f"invoice_{invoice_number}.pdf",
                    content=pdf_attachment,
                    content_type="application/pdf",
                )
            )

        try:
            result = await self.service.send_templated_email(
                to_addresses=customer_email,
                template_name="invoice",
                context=context,
                attachments=attachments,
            )

            logger.info(
                "Invoice email sent",
                customer_email=customer_email,
                invoice_number=invoice_number,
                has_pdf=bool(pdf_attachment),
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send invoice email",
                customer_email=customer_email,
                invoice_number=invoice_number,
                error=str(e),
            )
            raise

    async def send_restaurant_application_status(
        self,
        restaurant_email: str,
        restaurant_name: str,
        owner_name: str,
        application_status: str,
        status_message: str,
        next_steps: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send restaurant application status update

        Args:
            restaurant_email: Restaurant owner's email
            restaurant_name: Restaurant name
            owner_name: Owner's name
            application_status: Application status (approved, rejected, pending_review)
            status_message: Status message
            next_steps: List of next steps (optional)

        Returns:
            Send result dictionary
        """
        context = self._get_base_context({
            "owner_name": owner_name,
            "restaurant_name": restaurant_name,
            "application_status": application_status,
            "status_message": status_message,
            "next_steps": next_steps or [],
            "dashboard_url": "https://yourapp.com/restaurant/dashboard",
        })

        try:
            result = await self.service.send_templated_email(
                to_addresses=restaurant_email,
                template_name="restaurant_application_status",
                context=context,
            )

            logger.info(
                "Restaurant application status email sent",
                restaurant_email=restaurant_email,
                restaurant_name=restaurant_name,
                application_status=application_status,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send restaurant application status email",
                restaurant_email=restaurant_email,
                restaurant_name=restaurant_name,
                error=str(e),
            )
            raise

    async def send_delivery_assignment(
        self,
        driver_email: str,
        driver_name: str,
        order_id: UUID,
        order_number: str,
        pickup_address: str,
        delivery_address: str,
        customer_name: str,
        customer_phone: str,
        estimated_pickup_time: str,
        estimated_delivery_time: str,
        delivery_fee: float,
    ) -> Dict[str, Any]:
        """
        Send delivery assignment notification to driver

        Args:
            driver_email: Driver's email
            driver_name: Driver's name
            order_id: Order UUID
            order_number: Order number
            pickup_address: Restaurant pickup address
            delivery_address: Customer delivery address
            customer_name: Customer name
            customer_phone: Customer phone
            estimated_pickup_time: Estimated pickup time
            estimated_delivery_time: Estimated delivery time
            delivery_fee: Delivery fee for driver

        Returns:
            Send result dictionary
        """
        context = self._get_base_context({
            "driver_name": driver_name,
            "order_id": str(order_id),
            "order_number": order_number,
            "pickup_address": pickup_address,
            "delivery_address": delivery_address,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "estimated_pickup_time": estimated_pickup_time,
            "estimated_delivery_time": estimated_delivery_time,
            "delivery_fee": delivery_fee,
            "navigation_url": f"https://maps.google.com/?q={delivery_address}",
        })

        try:
            result = await self.service.send_templated_email(
                to_addresses=driver_email,
                template_name="delivery_assignment",
                context=context,
            )

            logger.info(
                "Delivery assignment email sent",
                driver_email=driver_email,
                order_id=order_id,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send delivery assignment email",
                driver_email=driver_email,
                order_id=order_id,
                error=str(e),
            )
            raise

    async def send_weekly_report(
        self,
        recipient_email: str,
        recipient_name: str,
        report_period: str,
        total_orders: int,
        total_revenue: float,
        total_customers: int,
        top_items: List[Dict[str, Any]],
        report_pdf: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Send weekly business report

        Args:
            recipient_email: Recipient's email
            recipient_name: Recipient's name
            report_period: Report period (e.g., "Week of Dec 1-7, 2024")
            total_orders: Total number of orders
            total_revenue: Total revenue
            total_customers: Total unique customers
            top_items: List of top selling items
            report_pdf: PDF report attachment (optional)

        Returns:
            Send result dictionary
        """
        context = self._get_base_context({
            "recipient_name": recipient_name,
            "report_period": report_period,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "top_items": top_items,
            "average_order_value": total_revenue / total_orders if total_orders > 0 else 0,
        })

        attachments = []
        if report_pdf:
            attachments.append(
                EmailAttachment(
                    filename=f"weekly_report_{report_period.replace(' ', '_')}.pdf",
                    content=report_pdf,
                    content_type="application/pdf",
                )
            )

        try:
            result = await self.service.send_templated_email(
                to_addresses=recipient_email,
                template_name="weekly_report",
                context=context,
                attachments=attachments,
            )

            logger.info(
                "Weekly report email sent",
                recipient_email=recipient_email,
                report_period=report_period,
                message_id=result.get("message_id"),
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to send weekly report email",
                recipient_email=recipient_email,
                report_period=report_period,
                error=str(e),
            )
            raise

    async def send_promotional_email(
        self,
        recipient_emails: List[str],
        subject: str,
        heading: str,
        message: str,
        cta_text: str,
        cta_url: str,
        promo_code: Optional[str] = None,
        expiry_date: Optional[datetime] = None,
        banner_image_url: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send promotional/marketing email

        Args:
            recipient_emails: List of recipient emails
            subject: Email subject
            heading: Email heading
            message: Promotional message
            cta_text: Call-to-action button text
            cta_url: Call-to-action URL
            promo_code: Promo code (optional)
            expiry_date: Promo expiry date (optional)
            banner_image_url: Banner image URL (optional)

        Returns:
            List of send results
        """
        context = self._get_base_context({
            "subject": subject,
            "heading": heading,
            "message": message,
            "cta_text": cta_text,
            "cta_url": cta_url,
            "promo_code": promo_code,
            "expiry_date": expiry_date.strftime("%B %d, %Y") if expiry_date else None,
            "banner_image_url": banner_image_url,
            "unsubscribe_url": "https://yourapp.com/unsubscribe",
        })

        results = []
        for email in recipient_emails:
            try:
                result = await self.service.send_templated_email(
                    to_addresses=email,
                    template_name="promotional",
                    context=context,
                )
                results.append(result)

                logger.info(
                    "Promotional email sent",
                    recipient_email=email,
                    subject=subject,
                    message_id=result.get("message_id"),
                )

            except Exception as e:
                logger.error(
                    "Failed to send promotional email",
                    recipient_email=email,
                    subject=subject,
                    error=str(e),
                )
                results.append({
                    "success": False,
                    "email": email,
                    "error": str(e),
                })

        return results


# Global helper instance
email_helpers = EmailHelpers()


async def get_email_helpers() -> EmailHelpers:
    """Dependency for getting email helpers in FastAPI routes"""
    return email_helpers