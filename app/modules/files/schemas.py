# app/modules/files/schemas.py

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    id: int
    s3_key: str
    s3_bucket: str
    original_filename: str
    content_type: str
    file_size: int
    file_extension: Optional[str]
    metadata_: Optional[Dict[str, Any]]
    is_public: bool
    uploaded_by_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PresignedUrlResponse(BaseModel):
    """Response schema for presigned URL."""
    url: str
    expires_in: int
    s3_key: str
    original_filename: str


class FileMetadataResponse(BaseModel):
    """Response schema for file metadata."""
    s3_key: str
    original_filename: str
    content_type: str
    file_size: int
    last_modified: datetime
    etag: str
    metadata_: Dict[str, Any]
    storage_class: Optional[str]


class FileDownloadResponse(BaseModel):
    """Response schema for file download info."""
    filename: str
    content_type: str
    file_size: int
    download_url: Optional[str] = None


class FileListResponse(BaseModel):
    """Response schema for listing files."""
    files: list[FileUploadResponse]
    total: int
    page: int
    size: int

