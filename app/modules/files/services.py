# app/modules/files/services.py

from typing import Optional, Dict, Any, BinaryIO, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.files.models import FileUpload
from app.modules.files.repository import FileRepository
from app.modules.files.s3_service import s3_service
from app.modules.files.utils import (
    file_validator, s3_key_generator
)
from app.modules.files.exceptions import FileNotFoundException

logger = get_logger(__name__)


class FileService:
    """Service for file management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FileRepository(db)

    async def upload_file(
        self, file_content: bytes, filename: str, content_type: str,
        folder: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None, is_public: bool = False,
        uploaded_by_id: Optional[int] = None
    ) -> FileUpload:
        """
        Upload file to S3 and create database record.

        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type
            folder: Optional folder path
            metadata: Optional metadata dictionary
            description: Optional file description
            is_public: Whether file should be publicly accessible
            uploaded_by_id: User ID who uploaded the file

        Returns:
            FileUpload object
        """
        # Validate file
        file_validator.validate_file_size(len(file_content))
        file_extension = file_validator.validate_file_extension(filename)

        # Detect and validate MIME type
        detected_mime = await file_validator.detect_mime_type(file_content, filename)
        file_validator.validate_mime_type(detected_mime)

        # Use detected MIME type if different from provided
        if detected_mime != content_type:
            logger.warning(
                "mime_type_mismatch",
                provided=content_type,
                detected=detected_mime,
                filename=filename
            )
            content_type = detected_mime

        # Generate S3 Kye
        s3_key, sanitized_filename = s3_key_generator.generate_key(
            filename=filename,
            folder=folder
        )

        # Upload to S3
        upload_result = await s3_service.upload_file(
            file_contents=file_content,
            s3_key=s3_key,
            content_type=content_type,
            metadata=metadata,
            is_public=is_public
        )

        # Create database record
        file_upload = FileUpload(
            s3_key=s3_key,
            s3_bucket=upload_result["bucket"],
            s3_region=upload_result['region'],
            s3_etag=upload_result['etag'],
            original_filename=sanitized_filename,
            content_type=content_type,
            file_size=len(file_content),
            file_extension=file_extension,
            metadata_=metadata,
            description=description,
            is_public=is_public,
            uploaded_by_id=uploaded_by_id
        )

        file_upload = await self.repo.create(file_upload)

        logger.info(
            "file_uploaded",
            file_id=file_upload.id,
            s3_key=s3_key,
            size=len(file_content)
        )

        return file_upload
    
    async def get_file(self, file_id: int) -> FileUpload:
        """Get file by ID."""
        file_upload = await self.repo.get_by_s3_key(s3_key=file_id)
        if not file_upload:
            raise FileNotFoundException(file_id=file_id)
        return file_upload
    
    async def get_file_by_key(self, s3_key: str) -> FileUpload:
        """Get file by S3 key."""
        file_upload = await self.repo.get_by_s3_key(s3_key)
        if not file_upload:
            raise FileNotFoundException(s3_key=s3_key)
        return file_upload

    async def list_files(
        self, skip: int = 0, limit: int = 100,
        uploaded_by_id: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> tuple[List[FileUpload], int]:
        """
        List files with pagination.

        Returns:
            Tuple of (files, total_count)
        """
        files = await self.repo.get_all(
            skip=skip,
            limit=limit,
            uploaded_by_id=uploaded_by_id,
            content_type=content_type
        )

        total = await self.repo.count(
            uploaded_by_id=uploaded_by_id,
            content_type=content_type
        )

        return files, total
    
    async def generate_presigned_url(
        self, file_id: int, expiry: Optional[int] = None,
        force_download: bool = False
    ) -> str:
        """
        Generate presigned URL for file.

        Args:
            file_id: File ID
            expiry: URL expiry in seconds
            force_download: If True, set content-disposition to force download

        Returns:
            Presigned URL string
        """
        file_upload = await self.get_file(file_id)

        # Set content disposition for downloads
        content_disposition = None
        if force_download:
            content_disposition = f"attachement; filename='{file_upload.original_filename}'"

        url = await s3_service.generate_presigned_url(
            s3_key=file_upload.s3_key,
            expiry=expiry,
            response_content_type=file_upload.content_type,
            response_content_disposition=content_disposition
        )

        logger.info("presigned_url_generated", file_id=file_id)

        return url
    
    async def get_file_metadata(self, file_id: int) -> Dict[str, Any]:
        """
        Get file metadata from S3.

        Args:
            file_id: File ID

        Returns:
            Dict with file metadata
        """
        file_upload = await self.get_file(file_id)

        # Get metadata from S3
        s3_metadata = await s3_service.get_object_metadata(file_upload.s3_key)

        # Combine with database metadata
        result = {
            'id': file_upload.id,
            's3_key': file_upload.s3_key,
            'original_filename': file_upload.original_filename,
            'content_type': file_upload.content_type,
            'file_size': file_upload.file_size,
            'file_extension': file_upload.file_extension,
            'description': file_upload.description,
            'uploaded_by_id': file_upload.uploaded_by_id,
            'created_at': file_upload.created_at,
            's3_metadata': s3_metadata['metadata'],
            's3_last_modified': s3_metadata['last_modified'],
            's3_etag': s3_metadata['etag'],
            'storage_class': s3_metadata.get('storage_class')
        }

        return result
    
    async def download_file_as_bytes(self, file_id: int) -> tuple[bytes, FileUpload]:
        """
        Download file as bytes.

        Args:
            file_id: File ID

        Returns:
            Tuple of (file_content, file_upload)
        """
        file_upload = await self.get_file(file_id)

        content = await s3_service.download_file_as_bytes(file_upload.s3_key)

        logger.info("file_downloaded_bytes", file_id=file_id)

        return content, file_upload
    
    async def download_file_as_object(self, file_id: int) -> tuple[BinaryIO, FileUpload]:
        """
        Download file as file-like object.

        Args:
            file_id: File ID

        Returns:
            Tuple of (file_object, file_upload)
        """
        file_upload = await self.get_file(file_id)

        file_obj = await s3_service.download_file_as_object(file_upload.s3_key)

        logger.info("file_downloaded_object", file_id=file_id)

        return file_obj, file_upload
    
    async def delete_file(self, file_id: int, hard_delete: bool = False) -> None:
        """
        Delete file from S3 and database.

        Args:
            file_id: File ID
            hard_delete: If True, permanently delete from S3 and database
        """
        file_upload = await self.get_file(file_id)

        if hard_delete:
            # Delete from S3
            await s3_service.delete_file(file_upload.s3_key)

            # Hard delete from database
            await self.repo.hard_delete(file_upload)

            logger.info("file_hard_deleted", file_id=file_id, s3_key=file_upload.s3_key)
        else:
            # Soft delete in database only
            await self.repo.delete(file_upload)

        logger.info("file_soft_deleted", file_id=file_id)

    async def update_file_metadata(
        self, file_id: int, metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> FileUpload:
        """
        Update file metadata in database.

        Args:
            file_id: File ID
            metadata: New metadata
            description: New description

        Returns:
            Updated FileUpload object
        """
        file_upload = await self.get_file(file_id)

        if metadata is not None:
            file_upload.metadata = metadata

        if description is not None:
            file_upload.description = description

        file_upload = await self.repo.update(file_upload)

        logger.info("file_metadata_updated", file_id=file_id)

        return file_upload
    
    async def copy_file(
        self, file_id: int, new_folder: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
    ) -> FileUpload:
        """
        Copy file to new location in S3.

        Args:
            file_id: Source file ID
            new_folder: New folder path
            new_metadata: New metadata for copied file

        Returns:
            New FileUpload object
        """
        source_file = await self.get_file(file_id)

        # Generate new S3 key
        new_s3_key, _ = s3_key_generator.generate_key(
            filename=source_file.original_filename,
            folder=new_folder
        )

        # Copy in S3
        copy_result = await s3_service.copy_file(
            source_key=source_file.s3_key,
            destination_key=new_s3_key,
            metadata=new_metadata
        )

        # Create new database record
        new_file = FileUpload(
            s3_key=new_s3_key,
            s3_bucket=source_file.s3_bucket,
            s3_region=source_file.s3_region,
            s3_etag=copy_result['etag'],
            original_filename=source_file.original_filename,
            content_type=source_file.content_type,
            file_size=source_file.file_size,
            file_extension=source_file.file_extension,
            metadata_=new_metadata or source_file.metadata,
            description=source_file.description,
            is_public=source_file.is_public,
            uploaded_by_id=source_file.uploaded_by_id
        )

        new_file = await self.repo.create(new_file)

        logger.info("file_copied", source_id=file_id, new_id=new_file.id, new_key=new_s3_key)

        return new_file
    
