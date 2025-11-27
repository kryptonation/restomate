# app/modules/users/router.py

import base64
from typing import List, Optional

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.users.services import UserService
from app.modules.users.schemas import *
from app.core.security import decode_token
from app.modules.users.exceptions import UnauthorizedException
from app.dependencies import ActiveUser, require_permission

router = APIRouter(prefix="/users", tags=["users"])
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


# ========== Dependencies ==========

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency to get user service"""
    return UserService(db)

async def get_current_user(
    request: Request,
    service: UserService = Depends(get_user_service)
):
    """Get current authenticated user from token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    token_data = decode_token(token)

    if not token_data or token_data.get("type") != "access":
        raise UnauthorizedException("Invalid token")
    
    user_id = int(token_data.get("sub"))
    return await service.get_user(user_id)

# ========== Authentication endpoints ==========

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """Register a new user"""
    return await service.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        role_id=user_data.role_id,
        send_verification_email=True
    )

@auth_router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    service: UserService = Depends(get_user_service)
):
    """Login and get access token"""
    result = await service.authenticate(
        email=login_data.email,
        password=login_data.password,
        totp_code=login_data.totp_code
    )
    return result

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    service: UserService = Depends(get_user_service)
):
    """Refresh access token."""
    return await service.refresh_access_token(refresh_data.refresh_token)

@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_data: RefreshTokenRequest,
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Logout from current session."""
    await service.logout(current_user.id, refresh_data.refresh_token)
    return {"message": "Logged out successfully."}

@auth_router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Logout from all sessions."""
    await service.logout_all_sessions(current_user.id)
    return {"message": "Logged out from all sessions"}

# ========== Password management endpoints ==========

@auth_router.post("/password/change", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Change user password."""
    return await service.change_password(
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

@auth_router.post("/password/reset-request", response_model=MessageResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    service: UserService = Depends(get_user_service)
):
    """Request password reset."""
    return await service.request_password_reset(reset_data.email)

@auth_router.post("/password/reset", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    service: UserService = Depends(get_user_service)
):
    """Reset password using token."""
    return await service.reset_password(
        token=reset_data.token,
        new_password=reset_data.new_password
    )

# ========== Email verification endpoints ==========

@auth_router.post("/email/send-verification", response_model=MessageResponse)
async def send_verification_email(
    email_data: EmailVerificationRequest,
    service: UserService = Depends(get_user_service)
):
    """Send email verification link."""
    return await service.send_verification_email(email_data.email)

@auth_router.post("/email/verify", response_model=MessageResponse)
async def verify_email(
    verify_data: EmailVerificationConfirm,
    service: UserService = Depends(get_user_service)
):
    """Verify email using token."""
    return await service.verify_email(verify_data.token)

# ========== 2FA endpoints ==========

@auth_router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """setup two-factor authentication."""
    result = await service.setup_2fa(current_user.id)

    # Convert QR code bytes to base64 for JSON response
    qr_code_base64 = base64.b64encode(result["qr_code"]).decode("utf-8")

    return {
        "secret": result["secret"],
        "qr_code_base64": qr_code_base64,
        "backup_codes": result["backup_codes"],
        "provisioning_uri": result["provisioning_uri"]
    }

@auth_router.post("/2fa/enable", response_model=BackupCodesResponse)
async def enable_2fa(
    enable_data: TwoFactorEnableRequest,
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Enable two-factor authentication after verification."""
    return await service.enable_2fa(current_user.id, enable_data.totp_code)

@auth_router.post("/2fa/disable", response_model=MessageResponse)
async def disable_2fa(
    disable_data: TwoFactorDisableRequest,
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Disable two-factor authentication."""
    return await service.disable_2fa(current_user.id, disable_data.password)

@auth_router.post("/2fa/regenerate-backup-codes", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    regen_data: BackupCodesResponse,
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Regenerate backup codes"""
    codes = await service.regenerate_backup_codes(current_user.id, regen_data.password)
    return {"backup_codes": codes}

# ========== User management endpoints ==========

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Update current user's profile."""
    return await service.update_user(
        user_id=current_user.id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        role_id=user_data.role_id
    )

@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: ActiveUser,
    service: UserService = Depends(get_user_service),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    _: None = Depends(require_permission("users", "read"))
):
    """List all users (admin only)."""
    # TODO: add permission check for admin
    return await service.list_users(skip=skip, limit=limit, is_active=is_active)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: ActiveUser,
    service: UserService = Depends(get_user_service),
    _: None = Depends(require_permission("users", "read"))
):
    """Get user by ID (admin only)."""
    # TODO: add permission check for admin
    return await service.get_user(user_id)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: ActiveUser,
    service: UserService = Depends(get_user_service),
    _: None = Depends(require_permission("users", "delete"))
):
    """Delete user (admin only)."""
    # TODO: add permission check for admin
    await service.delete_user(user_id)