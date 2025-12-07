# src/core/base_model.py

"""
Base models for SQLAlchemy and Pydantic
Includes UUID primary keys, timestamps, and audit fields
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


# ==============================================================================
# SQLAlchemy Base Models
# ==============================================================================

class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models
    Includes async support via AsyncAttrs
    """
    pass


class UUIDMixin:
    """Mixin for UUID primary key"""

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False,
        doc="Unique identifier"
    )


class TimestampMixin:
    """Mixin for timestamp fields"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        index=True, doc="Timestamp of record creation"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
        index=True, doc="Timestamp of last update"
    )


class AuditMixin:
    """Mixin for audit fields (who created/updated)"""

    created_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True, doc="User ID who created this record"
    )

    updated_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True, doc="User ID who last updated this record"
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""

    is_deleted: Mapped[bool] = mapped_column(
        default=False, nullable=False, index=True, doc="Soft delete flag"
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Timestamp of deletion"
    )

    deleted_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True, doc="User ID who deleted this record"
    )


class BaseModel(UUIDMixin, TimestampMixin, Base):
    """
    Base model with UUID, timestamps
    Use this for models that don't need audit fields
    """
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name (snake_case)"""
        import re
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    

class AuditedModel(UUIDMixin, TimestampMixin, AuditMixin, Base):
    """
    Base model with UUID, timestamps, and audit fields
    Use this for models that need to track who created/updated records
    """
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name (snake_case)"""
        import re
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    

class SoftDeleteModel(UUIDMixin, TimestampMixin, AuditMixin, SoftDeleteMixin, Base):
    """
    Base model with UUID, timestamps, audit fields, and soft delete
    Use this for models that should never be physically deleted
    """
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name (snake_case)"""
        import re
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    

# ==============================================================================
# Pydantic Base Models
# ==============================================================================

class BaseSchema(PydanticBaseModel):
    """
    Base Pydantic schema with common configuration
    """
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitary_types_allowed=True,
        str_strip_whitespace=True
    )


class UUIDSchema(BaseSchema):
    """Schema with UUID field"""
    id: UUID = Field(..., description="Unique identifier")


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields"""
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AuditSchema(BaseSchema):
    """Schema with audit fields"""
    created_by: Optional[UUID] = Field(None, description="Created by user ID")
    updated_by: Optional[UUID] = Field(None, description="Updated by user ID")


class SoftDeleteSchema(BaseSchema):
    """Schema with soft delete fields"""
    is_deleted: bool = Field(False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[UUID] = Field(None, description="Deleted by user ID")


class BaseResponseSchema(UUIDSchema, TimestampSchema):
    """
    Standard response schema with ID and timestamps
    Use this for basic response models
    """
    pass


class AuditedResponseSchema(UUIDSchema, TimestampSchema, AuditSchema):
    """
    Response schema with audit information
    Use this for models that track creation/update
    """
    pass


class SoftDeleteResponseSchema(UUIDSchema, TimestampSchema, AuditSchema, SoftDeleteSchema):
    """
    Response schema with all tracking fields including soft delete
    """
    pass


# ==============================================================================
# Pagination Schemas
# ==============================================================================

class PaginationParams(BaseSchema):
    """Standard pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseSchema):
    """Standard paginated response wrapper"""
    items: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


# ==============================================================================
# Response Wrappers
# ==============================================================================

class ResponseModel(BaseSchema):
    """Standard API response wrapper"""
    success: bool = Field(True, description="Request success status")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[dict] = Field(None, description="Response data")


class ErrorResponse(BaseSchema):
    """Standard error response"""
    success: bool = Field(False, description="Request success status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


