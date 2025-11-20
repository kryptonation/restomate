# app/modules/users/models.py

from typing import Optional
from datetime import datetime
import enum

from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(BaseModel):
    """User model."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False
    )

    # 2FA fields
    two_fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_fa_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    backup_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Password management
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"), nullable=True 
    )
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users", lazy="selectin")

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
    

class RefreshToken(BaseModel):
    """Refresh token model for JWT refresh tokens."""
    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken {self.id}>"
    

class PasswordResetToken(BaseModel):
    """Password reset token model."""
    __tablename__ = "password_reset_tokens"

    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken {self.id}>"
    

class EmailVerificationToken(BaseModel):
    """Email verification token model."""
    __tablename__ = "email_verification_tokens"

    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<EmailVerificationToken {self.id}>"
    

class SMSTemplate(BaseModel):
    """SMS template model for storing reusable SMS templates."""
    __tablename__ = "sms_templates"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<SMSTemplate {self.name}>"
    

class AuditLog(BaseModel):
    """Audit log for tracking user actions."""
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.resource}>"
    
