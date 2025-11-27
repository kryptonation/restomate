# app/modules/seeder/models.py

from typing import Optional
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Text, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class SeederStatus(str, Enum):
    """Seeder execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class SeederType(str, Enum):
    """Type of seeder operation."""
    INITIAL = "initial"
    UPDATE = "update"
    RESET = "reset"
    RESTORE = "restore"


class SeederExecution(BaseModel):
    """Track seeder execution history."""

    __tablename__ = "seeder_executions"

    seeder_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    seeder_type: Mapped[SeederType] = mapped_column(
        SQLEnum(SeederType), nullable=False
    )
    status: Mapped[SeederStatus] = mapped_column(
        SQLEnum(SeederStatus), default=SeederStatus.PENDING, nullable=False
    )

    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Backup information
    backup_s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    backup_file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Execution metadata
    executed_by_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    execution_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SeederExecution {self.seeder_name} - {self.status}>"
    
