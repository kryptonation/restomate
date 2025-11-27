# app/modules/seeder/schemas.py

from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.seeder.models import SeederStatus, SeederType


class SeederExecutionResponse(BaseModel):
    """Schema for seeder execution response."""
    id: int
    seeder_name: str
    seeder_type: SeederType
    status: SeederStatus
    records_created: int
    records_updated: int
    records_deleted: int
    backup_s3_key: Optional[str]
    backup_file_size: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    executed_by_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SeederExecutionRequest(BaseModel):
    """Schema for seeder execution request."""
    create_backup: bool = True


class SeederRestoreRequest(BaseModel):
    """Schema for database restore request."""
    s3_key: Optional[str] = None
    execution_id: Optional[int] = None


class SeederExecutionListResponse(BaseModel):
    """Schema for seeder execution List."""
    executions: list[SeederExecutionResponse]
    total: int
    page: int
    size: int


class SeederResultResponse(BaseModel):
    """Schema for seeder execution result."""
    success: bool
    backup_created: bool
    backup_s3_key: Optional[str]
    results: Dict[str, Any]


class DatabaseResetResponse(BaseModel):
    """Schema for database reset response."""
    success: bool
    backup_s3_key: str
    results: Dict[str, Any]


class DatabaseRestoreResponse(BaseModel):
    """Schema for database restore response."""
    success: bool
    s3_key: str
    tables_restored: int
    records_restored: int

