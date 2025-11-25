# app/modules/files/models.py

from typing import Optional

from sqlalchemy import String, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class FileUpload(BaseModel):
    """Model to track uploaded files."""
    __tablename__ = "file_uploads"

    # S3 Information
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    s3_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_region: Mapped[str] = mapped_column(String(50), nullable=False)
    s3_etag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # File information
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_extension: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Access Control
    is_public: Mapped[bool] = mapped_column(nullable=False, default=False)
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Status
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    virus_scanned: Mapped[bool] = mapped_column(default=False, nullable=False)
    virus_scan_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    def __repr__(self) -> str:
        return f"<FileUpload {self.original_filename} -> {self.s3_key}>"