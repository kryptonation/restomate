# app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_password_reset_token(email: str) -> str:
    """Create password reset token."""
    data = {"sub": email, "type": "password_reset"}
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_token_expire_minutes
    )
    data.update({"exp": expire})
    return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        logger.warning("token_decode_error", error=str(e))
        return None
    
