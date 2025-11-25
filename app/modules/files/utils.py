# app/modules/files/utils.py

import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, Tuple

import magic

from app.config import settings
from app.modules.files.exceptions import (
    FileValidationException, FileSizeExceededException,
    InvalidFileTypeException
)


class FileValidator:
    """Validator for file uploads."""

    @staticmethod
    def validate_file_size(file_size: int) -> None:
        """Validate file size"""
        if file_size > settings.s3_max_file_size_bytes:
            raise FileSizeExceededException(
                size=file_size, max_size=settings.s3_max_file_size_bytes
            )
        
    @staticmethod
    def validate_file_extension(filename: str) -> str:
        """Validate and extract file extension."""
        _, ext = os.path.splitext(filename)
        ext = ext.lstrip(".").lower()

        if not ext:
            raise FileValidationException("File has no extension.")
        
        if ext not in settings.s3_allowed_extensions_list:
            raise InvalidFileTypeException(
                file_type=ext, allowed_types=settings.s3_allowed_extensions_list
            )
        
        return ext
    
    @staticmethod
    def validate_mime_type(content_type: str) -> None:
        """Validate MIME type."""
        if content_type.lower() not in settings.s3_allowed_mime_types_list:
            raise InvalidFileTypeException(
                file_type=content_type, allowed_types=settings.s3_allowed_mime_types_list
            )
        
    @staticmethod
    async def detect_mime_type(file_content: bytes, filename: str) -> str:
        """Detect MIME type from file content."""
        # Use python-magic for accurate detection
        try:
            mime = magic.Magic(mime=True)
            detected_type = mime.from_buffer(file_content)
        except Exception:
            # Fallback to mimetypes
            detected_type, _ = mimetypes.guess_type(filename)
            detected_type = detected_type or "application/octet-stream"

        return detected_type
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to remove unsafe characters."""
        # Remove path separators and other unsafe characters
        unsafe_chars = ["/", "\\", "..", "<", ">", ":", '"', "|", "?", "*"]
        sanitized = filename

        for char in unsafe_chars:
            sanitized = sanitized.replace(char, "_")

        # Limit filename length
        name, ext = os.path.splitext(sanitized)
        max_name_length = 200
        if len(name) > max_name_length:
            name = name[:max_name_length]

        return f"{name}{ext}"
    

class S3KeyGenerator:
    """Generator for S3 keys with proper naming conventions."""

    @staticmethod
    def generate_key(
        filename: str, folder: Optional[str] = None, use_uuid: bool = None,
        preserve_filename: bool = None
    ) -> Tuple[str, str]:
        """
        Generate S3 key for file.

        Returns:
            Tuple of (s3_key, sanitized_filename)
        """
        use_uuid = use_uuid if use_uuid is not None else settings.s3_use_uuid_prefix
        preserve_filename = preserve_filename if preserve_filename is not None else settings.s3_preserve_filename

        # Sanitize original filename
        sanitized = FileValidator.sanitize_filename(filename)
        name, ext = os.path.splitext(sanitized)

        # Generate new filename
        if use_uuid:
            unique_id = str(uuid.uuid4())
            if preserve_filename:
                new_filename = f"{unique_id}_{name}{ext}"
            else:
                new_filename = f"{unique_id}{ext}"
        else:
            if preserve_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{timestamp}_{name}{ext}"
            else:
                new_filename = sanitized

        # Build folder structure
        if folder:
            prefix = folder
        elif settings.s3_folder_structure:
            now = datetime.now()
            prefix = settings.s3_folder_structure.format(
                year=now.year,
                month=f"{now.month:02d}",
                day=f"{now.day:02d}",
                hour=f"{now.hour:02d}"
            )
        else:
            prefix = ""

        # Combine prefix and filename
        if prefix:
            s3_key = f"{prefix}/{new_filename}"
        else:
            s3_key = new_filename

        return s3_key, sanitized
    
    @staticmethod
    def extract_filename_from_key(s3_key: str) -> str:
        """Extract filename from S3 key."""
        return os.path.basename(s3_key)
    

class MetadataParser:
    """Parser for S3 object metadata."""

    @staticmethod
    def parse_metadata(metadata: dict) -> dict:
        """Parse metadata and convert JSON strings to objects"""
        import json

        parsed = {}
        for key, value in metadata.items():
            # Try to parse as JSON
            if isinstance(value, str):
                try:
                    parsed[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    parsed[key] = value

            else:
                parsed[key] = value

        return parsed
    
    @staticmethod
    def prepare_metadata_for_s3(metadata: dict) -> dict:
        """Prepare metadata for S3 (convert to strings)."""
        import json

        prepared = {}
        for key, value in metadata.items():
            # S3 metadata values must be strings
            if isinstance(value, (dict, list)):
                prepared[key] = json.dumps(value)
            else:
                prepared[key] = str(value)

        return prepared
    

file_validator = FileValidator()
s3_key_generator = S3KeyGenerator()
metadata_parser = MetadataParser()

