# app/modules/files/repository.py

from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.modules.files.models import FileUpload
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileRepository:
    """Repository for file operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, file_id: int) -> Optional[FileUpload]:
        """Get file by ID."""
        stmt = select(FileUpload).where(
            and_(
                FileUpload.id == file_id,
                FileUpload.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_s3_key(self, s3_key: str) -> Optional[FileUpload]:
        """Get file by S3 key."""
        stmt = select(FileUpload).where(
            and_(
                FileUpload.s3_key == s3_key,
                FileUpload.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, skip: int = 0, limit: int = 100,
        uploaded_by_id: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> List[FileUpload]:
        """Get all files with filters."""
        stmt = select(FileUpload).where(FileUpload.is_deleted == False)

        if uploaded_by_id:
            stmt = stmt.where(FileUpload.uploaded_by_id == uploaded_by_id)

        if content_type:
            stmt = stmt.where(FileUpload.content_type.like(f"{content_type}%"))

        stmt = stmt.offset(skip).limit(limit).order_by(FileUpload.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    

    async def create(self, file_upload: FileUpload) -> FileUpload:
        """create a file record."""
        self.db.add(file_upload)
        await self.db.flush()
        await self.db.refresh(file_upload)

        logger.info(
            "file_record_created",
            file_id=file_upload.id,
            s3_key=file_upload.s3_key
        )

        return file_upload
    
    async def update(self, file_upload: FileUpload) -> FileUpload:
        """Update file record."""
        await self.db.flush()
        await self.db.refresh(file_upload)

        logger.info("file_record_updated", file_id=file_upload.id)

        return file_upload
    
    async def delete(self, file_upload: FileUpload) -> None:
        """soft delete file record."""
        file_upload.is_deleted = True
        await self.db.flush()
        await self.db.refresh(file_upload)

        logger.info("file_record_deleted", file_id=file_upload.id)

    async def hard_delete(self, file_upload: FileUpload) -> None:
        """Hard delete file record."""
        await self.db.delete(file_upload)
        await self.db.flush()

        logger.info("file_record_hard_deleted", file_id=file_upload.id)

    async def count(
        self, uploaded_by_id: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> int:
        """Count files with filters."""
        from sqlalchemy import func

        stmt = select(func.count(FileUpload.id)).where(
            FileUpload.is_deleted == False
        )

        if uploaded_by_id:
            stmt = stmt.where(FileUpload.uploaded_by_id == uploaded_by_id)

        if content_type:
            stmt = stmt.where(FileUpload.content_type.like(f"{content_type}%"))

        result = await self.db.execute(stmt)
        return result.scalar_one()
    
