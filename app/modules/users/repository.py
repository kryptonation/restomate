# app/modules/users/repository.py

from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.users.models import (
    User, RefreshToken, PasswordResetToken,
    EmailVerificationToken, AuditLog
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id).options(
            selectinload(User.role)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email).options(
            selectinload(User.role)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.username == username).options(
            selectinload(User.role)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[User]:
        """Get all users with pagination"""
        stmt = select(User).options(selectinload(User.role))

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        logger.info("user_created", user_id=user.id, email=user.email)
        return user
    
    async def update(self, user: User) -> User:
        """Update user."""
        await self.db.flush()
        await self.db.refresh(user)
        logger.info("user_updated", user_id=user.id, email=user.email)
        return user
    
    async def delete(self, user: User) -> None:
        """Delete user (soft delete)."""
        user.is_active = False
        user.status = "deleted"
        await self.db.flush()
        logger.info("user_deleted", user_id=user.id, email=user.email)

    async def increment_failed_login(self, user: User) -> User:
        """Increment failed login attempts."""
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 30 minutes
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            logger.warning("user_account_locked", user_id=user.id, email=user.email)

        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def reset_failed_login(self, user: User) -> User:
        """Reset failed login attempts"""
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def update_last_login(self, user: User) -> User:
        """Update last login timestamp."""
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    

class RefreshTokenRepository:
    """Repository for RefreshToken operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        stmt = select(RefreshToken).where(
            RefreshToken.token == token,
            RefreshToken.is_revoked == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, token: RefreshToken) -> RefreshToken:
        """Create a new refresh token."""
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token
    
    async def revoke(self, token: RefreshToken) -> None:
        """Revoke a refresh token."""
        token.is_revoked = True
        await self.db.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        """Revoke all refresh tokens for a user."""
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        for token in tokens:
            token.is_revoked = True

        await self.db.flush()

    async def delete_expired(self) -> int:
        """Delete expired tokens"""
        stmt = select(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        count = len(tokens)
        for token in tokens:
            await self.db.delete(token)

        await self.db.flush()
        return count
    

class PasswordResetTokenRepository:
    """Repository for PasswordResetToken operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token."""
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, token: PasswordResetToken) -> PasswordResetToken:
        """Create password reset token."""
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token
    
    async def mark_as_used(self, token: PasswordResetToken) -> None:
        """Mark token as used."""
        token.is_used = True
        await self.db.flush()

    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        count = len(tokens)
        for token in tokens:
            await self.db.delete(token)

        await self.db.flush()
        return count
    

class EmailVerificationTokenRepository:
    """Repository for EmailVerificationToken operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> Optional[EmailVerificationToken]:
        """Get email verification token."""
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token == token,
            EmailVerificationToken.is_used == False,
            EmailVerificationToken.expires_at > datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        """Create email verification token."""
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token
    
    async def mark_as_used(self, token: EmailVerificationToken) -> None:
        """Mark token as used."""
        token.is_used = True
        await self.db.flush()


class AuditLogRepository:
    """Repository for AuditLog operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, log: AuditLog) -> AuditLog:
        """Create audit log entry."""
        self.db.add(log)
        await self.db.flush()
        return log
    
    async def get_for_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for user."""
        stmt = (
            select(AuditLog).where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip).limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
