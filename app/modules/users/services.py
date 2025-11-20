# app/modules/users/services.py

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import json
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import (
    User, RefreshToken, PasswordResetToken,
    EmailVerificationToken, AuditLog, UserStatus
)
from app.modules.users.repository import (
    UserRepository, RefreshTokenRepository, PasswordResetTokenRepository,
    EmailVerificationTokenRepository, AuditLogRepository
)
from app.modules.users.exceptions import *
from app.modules.roles.services import RoleService
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, create_password_reset_token, decode_token
)
from app.utils.otp import otp_service
from app.utils.password import password_validator
from app.utils.email import email_service
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management and authentication."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.password_reset_repo = PasswordResetTokenRepository(db)
        self.email_verification_repo = EmailVerificationTokenRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.role_service = RoleService(db)

    # ========= User CRUD operations =========

    async def get_user(self, user_id: int) -> User:
        """Get user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id=user_id)
        return user
    
    async def get_user_by_email(self, email: str) -> User:
        """Get user by email."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundException(email=email)
        return user
    
    async def get_user_by_username(self, username: str) -> User:
        """Get user by username."""
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise UserNotFoundException(username=username)
        return user
    
    async def list_users(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[User]:
        """List all users."""
        return await self.user_repo.get_all(skip=skip, limit=limit, is_active=is_active)
    
    async def create_user(
        self, email: str, username: str, password: str,
        first_name: Optional[str] = None, last_name: Optional[str] = None,
        phone_number: Optional[str] = None, role_id: Optional[int] = None,
        send_verification_email: bool = True
    ) -> User:
        """Create a new user."""
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsException("email", email)
        
        # Check if username already exists
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise UserAlreadyExistsException("username", username)
        
        # Validate password strength
        is_valid, message = password_validator.validate_strength(password)
        if not is_valid:
            raise WeakPasswordException(message)
        
        # Check for common passwords
        if password_validator.check_common_passwords(password):
            raise WeakPasswordException("Password is too common.")
        
        # Verify role exists if provided
        if role_id:
            await self.role_service.get_role(role_id)

        # Create user
        user = User(
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role_id=role_id,
            password_changed_at=datetime.now(timezone.utc)
        )

        user = await self.user_repo.create(user)

        # Send verification email
        if send_verification_email:
            await self.send_verification_email(user.email)

        # Audit log
        await self._create_audit_log(
            user_id=user.id,
            action="user_created",
            resource="user",
            resource_id=str(user.id)
        )

        logger.info("user_service_created", user_id=user.id, email=user.email)
        return user
    
    async def update_user(
        self, user_id: int, first_name: Optional[str] = None,
        last_name: Optional[str] = None, phone_number: Optional[str] = None,
        role_id: Optional[int] = None
    ) -> User:
        """Update user information."""
        user = await self.get_user(user_id)

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone_number is not None:
            user.phone_number = phone_number
        if role_id is not None:
            await self.role_service.get_role(role_id)
            user.role_id = role_id

        user = await self.user_repo.update(user)

        await self._create_audit_log(
            user_id=user.id,
            action="user_updated",
            resource="user",
            resource_id=str(user.id)
        )

        logger.info("user_service_updated", user_id=user.id)
        return user
    
    async def delete_user(self, user_id: int) -> None:
        """Delete a user (soft delete)."""
        user = await self.get_user(user_id)
        await self.user_repo.delete(user)

        await self._create_audit_log(
            user_id=user.id,
            action="user_deleted",
            resource="user",
            resource_id=str(user.id)
        )

        logger.info("user_service_deleted", user_id=user_id)

    # ========= Authentication operations =========

    async def authenticate(
        self, email: str, password: str, totp_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate user and return tokens."""
        # Get user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsException()
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise AccountLockedException(user.locked_until.isoformat())
        
        # Verify password
        if not verify_password(password, user.password_hash):
            await self.user_repo.increment_failed_login(user)
            raise InvalidCredentialsException()
        
        # Check account status
        if not user.is_active or user.status != UserStatus.ACTIVE:
            raise AccountInactiveException()
        
        # Check email verification (Optional - can be disabled)
        # if not user.is_verified:
        #     raise EmailNotVerifiedException()

        # Check 2FA if enabled
        if user.two_fa_enabled:
            if not totp_code:
                raise TwoFactorRequiredException()
            
            if not await self.verify_2fa(user.id, totp_code):
                await self.user_repo.increment_failed_login(user)
                raise Invalid2FACodeException()
            
        # Reset failed login attempts
        await self.user_repo.reset_failed_login(user)
        await self.user_repo.update_last_login(user)

        # Generate tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token_str = create_refresh_token({"sub": str(user.id)})

        # Store refresh token
        refresh_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        )
        await self.refresh_token_repo.create(refresh_token)

        await self._create_audit_log(
            user_id=user.id,
            action="user_login",
            resource="auth",
            resource_id=str(user.id)
        )

        logger.info("user_authenticated", user_id=user.id, email=user.email)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "user": user
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token."""
        # Verify refresh token
        token_data = decode_token(refresh_token)
        if not token_data or token_data.get("type") != "refresh":
            raise InvalidTokenException("refresh token")
        
        # Check if token exists and is not revoked
        token_record = await self.refresh_token_repo.get_by_token(refresh_token)
        if not token_record:
            raise InvalidTokenException("refresh token")
        
        # Check expiration
        if token_record.expires_at < datetime.now(timezone.utc):
            raise InvalidTokenException("refresh token")
        
        # Get user
        user = await self.get_user(token_record.user_id)

        # Generate new access token
        access_token = create_access_token({"sub": str(user.id), "email": user.email})

        logger.info("access_token_refreshed", user_id=user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    async def logout(self, user_id: int, refresh_token: str) -> None:
        """Logout user by revoking refresh token."""
        token_record = await self.refresh_token_repo.get_by_token(refresh_token)
        if token_record:
            await self.refresh_token_repo.revoke(token_record)

        await self._create_audit_log(
            user_id=user_id,
            action="user_logout",
            resource="auth",
            resource_id=str(user_id)
        )

        logger.info("user_logged_out", user_id=user_id)

    async def logout_all_sessions(self, user_id: int) -> None:
        """Logout user from all sessions."""
        await self.refresh_token_repo.revoke_all_for_user(user_id)

        await self._create_audit_log(
            user_id=user_id,
            action="user_logout_all",
            resource="auth",
            resource_id=str(user_id)
        )

        logger.info("user_logged_out_all_sessions", user_id=user_id)

    # ========= Helper Methods =========

    async def _create_audit_log(
        self, user_id: Optional[int], action: str,
        resource: str, resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Create audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        await self.audit_repo.create(log)

    # ========= Two factor authentication =========

    async def setup_2fa(self, user_id: int) -> Dict[str, Any]:
        """
        Setup 2FA for user.
        Returns QR code and backup codes.
        """
        user = await self.get_user(user_id)

        if user.two_fa_enabled:
            raise TwoFactorAlreadyEnabledException()
        
        # Generate TOTP secret
        secret = otp_service.generate_secret()

        # Generate provisioning URI for QR code
        provisioning_uri = otp_service.generate_provisioning_uri(secret, user.email)

        # Generate QR code
        qr_code_bytes = otp_service.generate_qr_code(provisioning_uri)

        # Generate backup codes
        backup_codes = otp_service.generate_backup_codes()

        # Store secret and backup codes (not yet enabled)
        user.two_fa_secret = secret
        user.backup_codes = json.dumps(backup_codes)
        await self.user_repo.update(user)

        logger.info("2fa_setup_initiated", user_id=user.id)

        return {
            "secret": secret,
            "qr_code": qr_code_bytes,
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri
        }
    
    async def enable_2fa(self, user_id: int, totp_code: str) -> Dict[str, Any]:
        """Enable 2FA after verifying TOTP code."""
        user = await self.get_user(user_id)

        if user.two_fa_enabled:
            raise TwoFactorAlreadyEnabledException()
        
        if not user.two_fa_secret:
            raise ValidationException("2FA setup not initiated.")
        
        # Verfify TOTP code
        if not otp_service.verify_totp(user.two_fa_secret, totp_code):
            raise Invalid2FACodeException()
        
        # Enable 2FA
        user.two_fa_enabled = True
        await self.user_repo.update(user)

        await self._create_audit_log(
            user_id=user.id,
            action="2fa_enabled",
            resource="user",
            resource_id=str(user.id)
        )

        # Send confirmation email
        await email_service.send_templated_email(
            to_emails=[user.email],
            subject="Two-factor Authentication Enabled",
            template_path="users/templates/2fa_enabled.html",
            context={"username": user.username}
        )

        logger.info("2fa_enabled", user_id=user.id)

        return {
            "message": "Two-factor authentication enabled successfully",
            "backup_codes": json.loads(user.backup_codes) if user.backup_codes else []
        }
    
    async def disable_2fa(self, user_id: int, password: str) -> Dict[str, str]:
        """Disable 2FA after verifying password."""
        user = await self.get_user(user_id)

        if not user.two_fa_enabled:
            raise TwoFactorNotEnabledException()
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()
        
        # Disable 2FA
        user.two_fa_enabled = False
        user.two_fa_secret = None
        user.backup_codes = None
        await self.user_repo.update(user)

        await self._create_audit_log(
            user_id=user.id,
            action="2fa_disabled",
            resource="user",
            resource_id=str(user.id)
        )

        # Send notification email
        await email_service.send_templated_email(
            to_emails=[user.email],
            subject="Two-Factor Authentication Disabled",
            template_path="users/templates/2fa_disabled.html",
            context={"username": user.username}
        )

        logger.info("2fa_disabled", user_id=user.id)

        return {"message": "Two-factor authentication disabled successfully"}
    
    async def verify_2fa(self, user_id: int, code: str) -> bool:
        """Verify 2FA code (TOTP or backup code)."""
        user = await self.get_user(user_id)

        if not user.two_fa_enabled or not user.two_fa_secret:
            return False
        
        # Try TOTP verification
        if otp_service.verify_totp(user.two_fa_secret, code):
            return True
        
        # Try backup codes
        if user.backup_codes:
            backup_codes = json.loads(user.backup_codes)
            if code in backup_codes:
                # Remove used backup code
                backup_codes.remove(code)
                user.backup_codes = json.dumps(backup_codes)
                await self.user_repo.update(user)

                logger.info("backup_code_used", user_id=user.id)
                return True
            
        return False
    
    async def regenerate_backup_codes(self, user_id: int, password: str) -> List[str]:
        """Regenerate backup codes."""
        user = await self.get_user(user_id)

        if not user.two_fa_enabled:
            raise TwoFactorNotEnabledException()
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()
        
        # Generate new backup codes
        backup_codes = otp_service.generate_backup_codes()
        user.backup_codes = json.dumps(backup_codes)
        await self.user_repo.update(user)

        await self._create_audit_log(
            user_id=user.id,
            action="backup_codes_regenerated",
            resource="user",
            resource_id=str(user.id)
        )

        logger.info("backup_codes_regenerated", user_id=user.id)

        return backup_codes
    
    # ========= Password Management =========

    async def change_password(
        self, user_id: int, current_password: str,
        new_password: str
    ) -> Dict[str, str]:
        """Change user password."""
        user = await self.get_user(user_id)

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsException()

        # Validate new password strength
        is_valid, message = password_validator.validate_strength(new_password)
        if not is_valid:
            raise WeakPasswordException(message)
        
        # Check for common passwords
        if password_validator.check_common_passwords(new_password):
            raise WeakPasswordException("Password is too common.")
        
        # Check if resusing current password
        if verify_password(new_password, user.password_hash):
            raise PasswordReusedException()
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)

        # Revoke all refresh tokens (logout from all devices)
        await self.refresh_token_repo.revoke_all_for_user(user_id)

        await self._create_audit_log(
            user_id=user.id,
            action="password_changed",
            resource="user",
            resource_id=str(user.id)
        )

        # Send notification email
        await email_service.send_templated_email(
            to_emails=[user.email],
            subject="Password Changed",
            template_path="users/templates/password_changed.html",
            context={"username": user.username}
        )

        logger.info("password_changed", user_id=user.id)

        return {"message": "Password changed successfully"}
    
    async def request_password_reset(self, email: str) -> Dict[str, str]:
        """Request password reset."""
        user = await self.user_repo.get_by_email(email)

        # Always return success to prevent email enumeration
        if not user:
            logger.info("password_reset_requested_nonexistent_email", email=email)
            return {"message": "If the email exists, a password reset link has been sent."}
        
        # Generate reset token
        reset_token = create_password_reset_token(user.email)

        # Store token in the database
        token_record = PasswordResetToken(
            token=reset_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_expire_minutes)
        )
        await self.password_reset_repo.create(token_record)

        # Send reset email
        # TODO: Replace with actual domain url
        reset_link = f"https://yourapp.com/reset-password?token={reset_token}"
        await email_service.send_templated_email(
            to_emails=[user.email],
            subject="Password Reset Request",
            template_path="users/templates/reset_password.html",
            context={
                "username": user.username,
                "reset_link": reset_link,
                "expires_in": settings.password_reset_token_expire_minutes
            }
        )

        await self._create_audit_log(
            user_id=user.id,
            action="password_reset_requested",
            resource="user",
            resource_id=str(user.id)
        )

        logger.info("password_reset_requested", user_id=user.id, email=email)
        return {"message": "If the email exists, a password reset link has been sent."}
    
    async def reset_password(self, token: str, new_password: str) -> Dict[str, str]:
        """Reset password using token."""
        # Verify token
        token_record = await self.password_reset_repo.get_by_token(token)
        if not token_record:
            raise InvalidTokenException("password reset token")
        
        # Get user
        user = await self.get_user(token_record.user_id)

        # Validate new password
        is_valid, message = password_validator.validate_strength(new_password)
        if not is_valid:
            raise WeakPasswordException(message)
        
        # Check for common passwords
        if password_validator.check_common_passwords(new_password):
            raise WeakPasswordException("Password is too common.")
        
        # Check if reusing current password
        if verify_password(new_password, user.password_hash):
            raise PasswordReusedException()
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.user_repo.update(user)

        # Mark token as used
        await self.password_reset_repo.mark_as_used(token_record)

        # Revoke all refresh tokens
        await self.refresh_token_repo.revoke_all_for_user(user.id)

        await self._create_audit_log(
            user_id=user.id,
            action="password_reset",
            resource="user",
            resource_id=str(user.id)
        )

        # Send confirmation email
        await email_service.send_templated_email(
            to_emails=[user.email],
            subject="Password Reset Successful",
            template_path="users/templates/password_reset_success.html",
            context={"username": user.username}
        )

        logger.info("password_reset", user_id=user.id)

        return {"message": "Password reset successfully"}
    
    # ========= Email Verification =========

    async def send_verification_email(self, email: str) -> Dict[str, str]:
        """Send email verification link."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return {"message": "If the email exists, a verification link has been sent."}
        
        if user.is_verified:
            return {"message": "Email is already verified."}
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # Store token
        token_record = EmailVerificationToken(
            token=verification_token,
            email=user.email,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        await self.email_verification_repo.create(token_record)

        # Send verification email
        # TODO: Replace with actual domain url
        verification_link = f"https://yourapp.com/verify-email?token={verification_token}"
        await email_service.send_templated_email(
            to_emails=[user.email],
            subject="Verify your email",
            template_path="users/templates/verify_email.html",
            context={
                "username": user.username,
                "verification_link": verification_link
            }
        )

        logger.info("verification_email_sent", user_id=user.id, email=email)

        return {"message": "Verification email sent"}
    
    async def verify_email(self, token: str) -> Dict[str, str]:
        """Verify email using token."""
        token_record = await self.email_verification_repo.get_by_token(token)
        if not token_record:
            raise InvalidTokenException("verification token")
        
        # Get user
        user = await self.user_repo.get_by_email(token_record.email)
        if not user:
            raise UserNotFoundException(email=token_record.email)
        
        # Mark as verified
        user.is_verified = True
        await self.user_repo.update(user)

        # Mark token as used
        await self.email_verification_repo.mark_as_used(token_record)

        await self._create_audit_log(
            user_id=user.id,
            action="email_verified",
            resource="user",
            resource_id=str(user.id)
        )

        logger.info("email_verified", user_id=user.id, email=user.email)

        return {"message": "Email verified successfully"}
    




