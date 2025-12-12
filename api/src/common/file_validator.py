# src/common/file_validator.py

"""
Production-grade File Validation Utility
Validates file size, type, content, and security with centralized configuration
"""

import hashlib
import imghdr
import mimetypes
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class FileCategory(str, Enum):
    """File categories for different use cases"""
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    SPREADSHEET = "spreadsheet"
    ANY = "any"


@dataclass
class FileValidationConfig:
    """
    File validation configuration for different categories
    """
    category: FileCategory
    allowed_extensions: Set[str]
    allowed_mime_types: Set[str]
    max_size_bytes: int
    min_size_bytes: int = 0
    check_content: bool = True
    description: str = ""

    def __post_init__(self):
        """Normalize extensions to lowercase with dot prefix"""
        self.allowed_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in self.allowed_extensions
        }


class FileValidationResult:
    """
    Result of file validation with detailed information
    """

    def __init__(
        self, is_valid: bool, file_path: Optional[str] = None,
        file_name: Optional[str] = None, file_size: Optional[int] = None,
        file_extension: Optional[str] = None, detected_mime_type: Optional[str] = None,
        category: Optional[FileCategory] = None, errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
    ):
        self.is_valid = is_valid
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.file_extension = file_extension
        self.detected_mime_type = detected_mime_type
        self.category = category
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}

    def __bool__(self) -> bool:
        """Allow boolean checks: if validation_result:"""
        return self.is_valid
    
    def __repr__(self) -> str:
        return (
            f"FileValidationResult(is_valid={self.is_valid}, "
            f"file_name={self.file_name}, errors={len(self.errors)})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_valid": self.is_valid,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_extension": self.file_extension,
            "detected_mime_type": self.detected_mime_type,
            "category": self.category.value if self.category else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }
    

class FileValidator:
    """
    Production-grade file validator with centralized configuration

    Features:
    - File size validation
    - Extension validation
    - MIME type detection and validation
    - Content-based validation (magic numbers)
    - Image validation (dimensions, format)
    - Security checks (executable detection, script injection)
    - Hash calculation
    - Metadata extraction
    - Category-based validation
    - Centralized configuration from settings
    """

    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        '.exe', '.dll', '.bat', '.cmd', '.com', '.scr', '.pif',
        '.app', '.deb', '.rpm', '.dmg', '.pkg', '.run',
        '.vbs', '.vbe', '.js', '.jse', '.ws', '.wsf', '.wsh',
        '.ps1', '.ps2', '.psc1', '.psc2', '.msh', '.msh1', '.msh2',
        '.scf', '.lnk', '.inf', '.reg', '.msi', '.msp', '.cpl',
        '.jar', '.sh', '.bash', '.csh', '.ksh', '.command',
    }

    # Default validation configurations
    DEFAULT_CONFIGS = {
        FileCategory.IMAGE: FileValidationConfig(
            category=FileCategory.IMAGE,
            allowed_extensions={'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'},
            allowed_mime_types={
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'image/bmp', 'image/svg+xml', 'image/x-icon'
            },
            max_size_bytes=10 * 1024 * 1024,  # 10 MB
            check_content=True,
            description="Image files for menus, profiles, restaurants"
        ),
        FileCategory.DOCUMENT: FileValidationConfig(
            category=FileCategory.DOCUMENT,
            allowed_extensions={'.pdf', '.doc', '.docx', '.txt', '.rtf'},
            allowed_mime_types={
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain',
                'application/rtf'
            },
            max_size_bytes=20 * 1024 * 1024,  # 20 MB
            check_content=True,
            description="Documents for licenses, contracts, reports"
        ),
        FileCategory.SPREADSHEET: FileValidationConfig(
            category=FileCategory.SPREADSHEET,
            allowed_extensions={'.xls', '.xlsx', '.csv', '.ods'},
            allowed_mime_types={
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                'application/vnd.oasis.opendocument.spreadsheet'
            },
            max_size_bytes=15 * 1024 * 1024,  # 15 MB
            check_content=True,
            description="Spreadsheets for inventory, reports, analytics"
        ),
        FileCategory.VIDEO: FileValidationConfig(
            category=FileCategory.VIDEO,
            allowed_extensions={'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'},
            allowed_mime_types={
                'video/mp4', 'video/x-msvideo', 'video/quicktime',
                'video/x-ms-wmv', 'video/x-flv', 'video/webm'
            },
            max_size_bytes=100 * 1024 * 1024,  # 100 MB
            check_content=False,  # Skip content check for large files
            description="Video files for promotions, tutorials"
        ),
        FileCategory.AUDIO: FileValidationConfig(
            category=FileCategory.AUDIO,
            allowed_extensions={'.mp3', '.wav', '.ogg', '.m4a', '.flac'},
            allowed_mime_types={
                'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/flac'
            },
            max_size_bytes=20 * 1024 * 1024,  # 20 MB
            check_content=False,
            description="Audio files for promotional content"
        ),
        FileCategory.ARCHIVE: FileValidationConfig(
            category=FileCategory.ARCHIVE,
            allowed_extensions={'.zip', '.tar', '.gz', '.rar', '.7z'},
            allowed_mime_types={
                'application/zip', 'application/x-tar', 'application/gzip',
                'application/x-rar-compressed', 'application/x-7z-compressed'
            },
            max_size_bytes=50 * 1024 * 1024,  # 50 MB
            check_content=True,
            description="Archive files for bulk uploads"
        ),
    }

    # Magic numbers for content-based validation
    MAGIC_NUMBERS = {
        'image/jpeg': [b'\xFF\xD8\xFF'],
        'image/png': [b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'],
        'image/gif': [b'GIF87a', b'GIF89a'],
        'application/pdf': [b'%PDF-'],
        'application/zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'video/mp4': [b'\x00\x00\x00\x18ftypmp4', b'\x00\x00\x00\x1Cftypmp42'],
    }

    def __init__(
        self, custom_configs: Optional[Dict[FileCategory, FileValidationConfig]] = None
    ):
        """
        Initialize file validator

        Args:
            custom_configs: Custom validation configurations to override defaults
        """
        self.configs = self.DEFAULT_CONFIGS.copy()

        if custom_configs:
            self.configs.update(custom_configs)

        # Load configuration from settings
        self._load_settings_config()

        logger.info(
            "File validator initialized",
            categories=list(self.configs.keys()),
        )

    def _load_settings_config(self):
        """Load validation configuration from application settings"""
        # Override with settings if available
        if hasattr(settings, "max_upload_size"):
            # Update max sizes from settings
            for config in self.configs.values():
                if config.max_size_bytes > settings.max_upload_size:
                    config.max_size_bytes = settings.max_upload_size

        if hasattr(settings, "allowed_extensions"):
            # Parse allowed extensions from settings
            allowed_exts = settings.allowed_extensions.split(",")
            allowed_exts = {f".{ext.strip().lower()}" for ext in allowed_exts}

            # Update image config with settings
            if FileCategory.IMAGE in self.configs:
                self.configs[FileCategory.IMAGE].allowed_extensions = (
                    self.configs[FileCategory.IMAGE].allowed_extensions & allowed_exts
                )

    def get_config(self, category: FileCategory) -> FileValidationConfig:
        """
        Get validation configuration for category

        Args:
            category: File category

        Returns:
            FileValidationConfig for the category
        """
        if category not in self.configs:
            raise ValueError(f"No configuration found for category: {category}")
        
        return self.configs[category]
    
    def _detect_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Detect MIME type using multiple methods

        Args:
            file_path: Path to file

        Returns:
            Detected MIME type or None
        """
        # Method 1: Using mimetypes module (extension-based)
        mime_type, _ = mimetypes.guess_type(str(file_path))

        if mime_type:
            logger.debug("MIME type detected (extension)", mime_type=mime_type)
            return mime_type
        
        # Method 2: Check magic numbers (content-based)
        try:
            with open(file_path, "rb") as f:
                header = f.read(32)

                for mime, signatures in self.MAGIC_NUMBERS.items():
                    for signature in signatures:
                        if header.startswith(signature):
                            logger.debug("MIME type detected (magic)", mime_type=mime)
                            return mime
        except Exception as e:
            logger.warning("Failed to read file header", error=str(e))

        # Method 3: Image-specific detection using imghdr
        if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
            try:
                img_type = imghdr.what(file_path)
                if img_type:
                    mime_type = f"image/{img_type}"
                    logger.debug("MIME type detected (imghdr)", mime_type=mime_type)
                    return mime_type
            except Exception as e:
                logger.warning("imghdr detection failed", error=str(e))

        return None
    
    def _check_dangerous_content(self, file_path: Path) -> List[str]:
        """
        Check for potentially dangerous content

        Args:
            file_path: Path to file

        Returns:
            List of warnings
        """
        warnings = []

        try:
            # Check for script tags in text files
            if file_path.suffix.lower() in {'.txt', '.html', '.htm', '.xml', '.svg'}:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(10000)

                    dangerous_patterns = [
                        '<script', 'javascript:', 'onerror=', 'onclick=',
                        'onload=', '<iframe', '<embed', '<object'
                    ]

                    for pattern in dangerous_patterns:
                        if pattern in content.lower():
                            warnings.append(f"Potentially dangerous content detected: {pattern}")

        except Exception as e:
            logger.warning("Content check failed", error=str(e))

        return warnings
    
    def _validate_image_dimensions(
        self, file_path: Path, max_width: Optional[int] = None, max_height: Optional[int] = None,
    ) -> List[str]:
        """
        Validate image dimensions (requires PIL/Pillow)

        Args:
            file_path: Path to image file
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels

        Returns:
            List of errors
        """
        errors = []

        try:
            from PIL import Image

            with Image.open(file_path) as img:
                width, height = img.size

                if max_width and width > max_width:
                    errors.append(f"Image width {width}px exceeds maximum {max_width}px")

                if max_height and height > max_height:
                    errors.append(f"Image height {height}px exceeds maximum {max_height}px")

                # Store dimensions in metadata
                return errors, {"width": width, "height": height, "format": img.format}
            
        except ImportError:
            logger.warning("PIL/Pillow not installed, skipping image dimension validation")
            return errors, {}
        except Exception as e:
            logger.warning("Image dimension validation failed", error=str(e))
            return errors, {}
        
    def _calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> Optional[str]:
        """
        Calculate file hash

        Args:
            file_path: Path to file
            algorithm: Hash algorithm (md5, sha1, sha256)

        Returns:
            Hash string or None
        """
        try:
            hash_obj = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()
        
        except Exception as e:
            logger.warning("Hash calculation failed", error=str(e))
            return None
        
    def validate_file(
        self, file_path: Union[str, Path], category: FileCategory, check_dimensions: bool = False,
        max_width: Optional[int] = None, max_height: Optional[int] = None, calculate_hash: bool = False,
    ) -> FileValidationResult:
        """
        Validate file against category configuration

        Args:
            file_path: Path to file
            category: File category for validation
            check_dimensions: Whether to check image dimensions
            max_width: Maximum image width
            max_height: Maximum image height
            calculate_hash: Whether to calculate file hash

        Returns:
            FileValidationResult with validation details
        """
        file_path = Path(file_path)
        errors = []
        warnings = []
        metadata = {}

        # Check if file exists
        if not file_path.exists():
            errors.append("File does not exist")
            return FileValidationResult(
                is_valid=False,
                file_path=str(file_path),
                file_name=file_path.name,
                errors=errors,
            )
        
        # Get file info
        file_size = file_path.stat().st_size
        file_extension = file_path.suffix.lower()
        file_name = file_path.name

        # Get validation config
        try:
            config = self.get_config(category)
        except ValueError as e:
            errors.append(str(e))
            return FileValidationResult(
                is_valid=False,
                file_path=str(file_path),
                file_name=file_name,
                file_size=file_size,
                file_extension=file_extension,
                errors=errors,
            )
        
        # Validate file extension
        if file_extension not in config.allowed_extensions:
            errors.append(
                f"File extension '{file_extension}' not allowed. "
                f"Allowed: {'. '.join(sorted(config.allowed_extensions))}"
            )

        # Check for dangerous extensions
        if file_extension in self.DANGEROUS_EXTENSIONS:
            errors.append(f"Dangerous file extension '{file_extension}' not allowed for security reasons.")

        # Validate file size
        if file_size < config.min_size_bytes:
            errors.append(
                f"File size {file_size} bytes is smaller than minimum allowed {config.min_size_bytes} bytes."
            )

        if file_size > config.max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            max_mb = config.max_size_bytes / (1024 * 1024)
            errors.append(
                f"File size {size_mb:.2f}MB exceeds maximum {max_mb:.2f}MB"
            )

        # Detect MIME type
        detected_mime = self._detect_mime_type(file_path)

        if detected_mime:
            metadata["detected_mime_type"] = detected_mime

            # Validate MIME type
            if config.check_content and detected_mime not in config.allowed_mime_types:
                errors.append(
                    f"MIME type '{detected_mime}' not allowed. "
                    f"Allowed: {', '.join(sorted(config.allowed_mime_types))}"
                )

            # Check for MIME type mismatch
            expected_mime, _ = mimetypes.guess_type(file_name)
            if expected_mime and detected_mime != expected_mime:
                warnings.append(
                    f"MIME type mismatch: extension suggests '{expected_mime}' "
                    f"but content is '{detected_mime}'"
                )
        else:
            if config.check_content:
                warnings.append("Could not detect MIME type from file content")

        # Check for dangerous content
        if config.check_content:
            content_warnings = self._check_dangerous_content(file_path)
            warnings.extend(content_warnings)

        # Validate image dimensions
        if check_dimensions and category == FileCategory.IMAGE:
            dim_errors, dim_metadata = self._validate_image_dimensions(
                file_path, max_width, max_height
            )
            errors.extend(dim_errors)
            metadata.update(dim_metadata)

        # Calculate file hash
        if calculate_hash:
            file_hash = self._calculate_file_hash(file_path)
            if file_hash:
                metadata["sha256"] = file_hash

        # Log validation result
        is_valid = len(errors) == 0

        log_method = logger.info if is_valid else logger.warning
        log_method(
            "File validation completed",
            file_name=file_name,
            category=category.value,
            is_valid=is_valid,
            errors=len(errors),
            warnings=len(warnings),
        )

        return FileValidationResult(
            is_valid=is_valid,
            file_path=str(file_path),
            file_name=file_name,
            file_size=file_size,
            file_extension=file_extension,
            detected_mime_type=detected_mime,
            category=category,
            errors=errors,
            warnings=warnings,
            metadata=metadata,
        )
    
    def validate_upload(
        self, file_content: bytes, filename: str, category: FileCategory,
        save_to: Optional[Path] = None,
    ) -> FileValidationResult:
        """
        Validate uploaded file content

        Args:
            file_content: File content as bytes
            filename: Original filename
            category: File category
            save_to: Optional path to save validated file

        Returns:
            FileValidationResult
        """
        import tempfile

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_file.write(file_content)
            temp_path = Path(temp_file.name)

        try:
            # Validate temporary file
            result = self.validate_file(
                file_path=temp_path, category=category
            )

            # Save to destination if provided and valid
            if result.is_valid and save_to:
                save_to = Path(save_to)
                save_to.parent.mkdir(parents=True, exist_ok=True)
                temp_path.rename(save_to)
                result.file_path = str(save_to)
                logger.info("Validated file saved", destination=str(save_to))
            else:
                # Clean up temp file
                temp_path.unlink()

            return result
        
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()

            logger.error("File upload validation failed", error=str(e))
            raise

    def validate_fastapi_upload(
        self, file: Any, category: FileCategory,
        save_to: Optional[Path] = None,
    ) -> FileValidationResult:
        """
        Validate FastAPI UploadFile

        Args:
            file: FastAPI UploadFile object
            category: File category
            save_to: Optional path to save validated file

        Returns:
            FileValidationResult
        """
        # Read file content
        content = file.file.read()

        # Reset file pointer
        file.file.seek(0)

        # Validate
        return self.validate_upload(
            file_content=content,
            filename=file.filename,
            category=category,
            save_to=save_to,
        )
    

# Global validator instance
file_validator = FileValidator()


def get_file_validator() -> FileValidator:
    """Dependency for getting file validator in FastAPI routes"""
    return file_validator

            


    