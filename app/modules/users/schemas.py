# app/modules/users/schemas.py

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.modules.users.models import UserStatus
from app.modules.roles.schemas import RoleResponse


# =========== User Schemas =============

class UserBase(BaseModel):
    """Base schema for user"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=128)
    role_id: Optional[int] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
    

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    role_id: Optional[int] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    status: UserStatus
    two_fa_enabled: bool
    role: Optional[RoleResponse]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========== Authentication schemas =============

class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6)


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"


# =========== Password management schemas =============


class PasswordChangeRequest(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# =========== 2FA Schemas =============

class TwoFactorSetupResponse(BaseModel):
    """Schema for 2FA setup response"""
    secret: str
    qr_code_base64: str
    backup_codes: List[str]
    provisioning_uri: str


class TwoFactorEnableRequest(BaseModel):
    """Schema for enabling 2FA"""
    totp_code: str = Field(..., min_length=6, max_length=6)


class TwoFactorDisableRequest(BaseModel):
    """Schema for disabling 2FA"""
    password: str


class TwoFactorVerifyRequest(BaseModel):
    """Schema for verifying 2FA code"""
    code: str = Field(..., min_length=6, max_length=6)


class BackupCodeRegenerateRequest(BaseModel):
    """Schema for regenerating backup codes"""
    password: str


class BackupCodesResponse(BaseModel):
    """Schema for backup codes response"""
    backup_codes: List[str]


# =========== Email verification schemas =============

class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Schema for confirming email verification"""
    token: str


# =========== Response schemas =============


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: int
    action: str
    resource: str
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

