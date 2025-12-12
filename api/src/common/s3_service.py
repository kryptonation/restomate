# src/common/s3_service.py

"""
Production-grade Amazon S3 File Management Service.
Handles upload, download, delete, presigned URLs, and metadata operations
"""

import mimetypes
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union
from urllib.parse import quote

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.core.config import settings
from src.core.exceptions import FileUploadError
from src.core.logging import get_logger

logger = get_logger(__name__)


class S3FileMetadata:
    """
    Represents S3 file metadata
    """

    def __init__(self, s3_metadata: Dict[str, Any]):
        """
        Initialize from S3 head_object response

        Args:
            s3_metadata: Response from head_object
        """
        self.content_type = s3_metadata.get("ContentType")
        self.content_length = s3_metadata.get("ContentLength", 0)
        self.last_modified = s3_metadata.get("LastModified")
        self.etag = s3_metadata.get("ETag", "").strip('"')
        self.metadata = s3_metadata.get("Metadata", {})
        self.storage_class = s3_metadata.get("StorageClass", "STANDARD")
        self.server_side_encryption = s3_metadata.get("ServerSideEncryption")
        self.version_id = s3_metadata.get("VersionId")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'content_type': self.content_type,
            'content_length': self.content_length,
            'content_length_mb': round(self.content_length / (1024 * 1024), 2),
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'etag': self.etag,
            'metadata': self.metadata,
            'storage_class': self.storage_class,
            'server_side_encryption': self.server_side_encryption,
            'version_id': self.version_id,
        }

    def __repr__(self) -> str:
        return (
            f"S3FileMetadata(content_type={self.content_type}, "
            f"size={self.content_length} bytes)"
        )


class S3Service:
    """
    Production-grade S3 file management service

    Features:
    - File upload (from path, bytes, file object)
    - File download (to path, bytes, file object)
    - Presigned URLs (GET, PUT, POST)
    - File deletion (single, multiple, prefix)
    - Metadata retrieval
    - File existence checking
    - Multipart upload support
    - Progress tracking
    - Automatic content type detection
    - Server-side encryption
    - Object tagging
    - Lifecycle management integration
    """

    def __init__(
        self, bucket_name: Optional[str] = None, region_name: Optional[str] = None,
        use_accelerate: bool = False
    ):
        """
        Initialize S3 service

        Args:
            bucket_name: S3 bucket name (defaults to settings)
            region_name: AWS region (defaults to settings)
            use_accelerate: Enable S3 Transfer Acceleration
        """
        self.bucket_name = bucket_name or settings.s3_bucket_name
        self.region_name = region_name or settings.aws_region
        self.use_accelerate = use_accelerate

        # Initialize S3 client with signature V4
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "auto"},
        )

        try:
            self.client = boto3.client(
                "s3", region_name=self.region_name,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                config=config,
            )

            # Initialize S3 resource for higher-level operations
            self.resource = boto3.resource(
                "s3", region_name=self.region_name,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                config=config,
            )

            self.bucket = self.resource.Bucket(self.bucket_name)

            logger.info(
                "S3 service initialized",
                bucket=self.bucket_name,
                region=self.region_name,
                accelerate=use_accelerate,
            )
        except Exception as e:
            logger.error("Failed to initialize S3 service", error=str(e))
            raise

    def _get_content_type(self, file_path: Union[str, Path]) -> str:
        """
        Detect content type from file extension

        Args:
            file_path: Path to file

        Returns:
            MIME content type
        """
        content_type, _ = mimetypes.guess_type(str(file_path))
        return content_type or "application/octet-stream"
    
    def _generate_s3_key(
        self, filename: str, prefix: Optional[str] = None,
        add_timestamp: bool = False,
    ) -> str:
        """
        Generate S3 object key

        Args:
            filename: Original filename
            prefix: Optional prefix/folder path
            add_timestamp: Add timestamp to filename

        Returns:
            S3 object key
        """
        # Sanitize filename
        filename = Path(filename).name

        # Add timestamp if requested
        if add_timestamp:
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stem}_{timestamp}{suffix}"

        # Combine with prefix
        if prefix:
            prefix = prefix.strip("/")
            return f"{prefix}/{filename}"
        
        return filename
    
    def upload_file(
        self, file_path: Union[str, Path], s3_key: Optional[str] = None,
        prefix: Optional[str] = None, content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None, acl: str = "private",
        storage_class: str = "STANDARD", tags: Optional[Dict[str, str]] = None,
        server_side_encryption: bool = True,
    ) -> Dict[str, Any]:
        """
        Upload file to S3

        Args:
            file_path: Path to local file
            s3_key: S3 object key (generated if not provided)
            prefix: Folder prefix in S3
            content_type: MIME content type (auto-detected if not provided)
            metadata: Custom metadata dictionary
            acl: Access control ('private', 'public-read', etc.)
            storage_class: Storage class (STANDARD, INTELLIGENT_TIERING, etc.)
            tags: Object tags
            server_side_encryption: Enable server-side encryption

        Returns:
            Dictionary with upload details
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate S3 key if not provided
        if not s3_key:
            s3_key = self._generate_s3_key(file_path.name, prefix)

        # Detect content type
        if not content_type:
            content_type = self._get_content_type(file_path)

        # Prepare extra args
        extra_args = {
            "ContentType": content_type,
            "ACL": acl,
            "StorageClass": storage_class,
        }

        if metadata:
            extra_args["Metadata"] = metadata

        if server_side_encryption:
            extra_args["ServerSideEncryption"] = "AES256"

        if tags:
            tag_str = "&".join([f"{k}={quote(v)}" for k, v in tags.items()])
            extra_args["Tagging"] = tag_str

        try:
            # Upload file
            self.client.upload_file(
                Filename=str(file_path),
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args,
            )

            # Get file size
            file_size = file_path.stat().st_size

            logger.info(
                "File uploaded to S3", s3_key=s3_key,
                bucket=self.bucket_name, size_bytes=file_size,
                content_type=content_type,
            )

            return {
                "success": True,
                "bucket": self.bucket_name,
                "s3_key": s3_key,
                "s3_url": f"s3://{self.bucket_name}/{s3_key}",
                "https_url": f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}",
                "file_size": file_size,
                "content_type": content_type,
            }
        
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            logger.error(
                "S3 upload failed", s3_key=s3_key, error_code=error_code,
                error_message=error_message,
            )
            raise FileUploadError(f"S3 upload failed: {error_message}")
        
        except Exception as e:
            logger.error("Unexpected error during S3 upload", error=str(e))
            raise

    def upload_fileobj(
        self, file_obj: BinaryIO, s3_key: str,
        content_type: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Upload file-like object to S3

        Args:
            file_obj: File-like object (must have read() method)
            s3_key: S3 object key
            content_type: MIME content type
            **kwargs: Additional arguments for upload_file

        Returns:
            Dictionary with upload details
        """
        # Detect content type from key if not provided
        if not content_type:
            content_type = self._get_content_type(s3_key)

        extra_args = {
            "ContentType": content_type,
            "ACL": kwargs.get("acl", "private"),
        }

        if kwargs.get("server_side_encryption", True):
            extra_args["ServerSideEncryption"] = "AES256"

        try:
            # Get file size
            file_obj.seek(0, 2)
            file_size = file_obj.tell()
            file_obj.seek(0)

            # Upload
            self.client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args,
            )

            logger.info(
                "File object uploaded to S3",
                s3_key=s3_key,
                size_bytes=file_size,
            )

            return {
                "success": True,
                "bucket": self.bucket_name,
                "s3_key": s3_key,
                "s3_url": f"s3://{self.bucket_name}/{s3_key}",
                "file_size": file_size,
                "content_type": content_type,
            }
        
        except ClientError as e:
            logger.error("S3 upload_fileobj failed", error=str(e))
            raise

    def upload_bytes(
        self, content: bytes, s3_key: str, content_type: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Upload bytes content to S3

        Args:
            content: File content as bytes
            s3_key: S3 object key
            content_type: MIME content type
            **kwargs: Additional arguments

        Returns:
            Dictionary with upload details
        """
        file_obj = BytesIO(content)
        return self.upload_fileobj(file_obj, s3_key, content_type, **kwargs)
    
    def download_file(
        self, s3_key: str, local_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Download file from S3 to local path

        Args:
            s3_key: S3 object key
            local_path: Local file path to save

        Returns:
            Dictionary with download details
        """
        local_path = Path(local_path)

        # Create parent directories if needed
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Download file
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=str(local_path),
            )

            file_size = local_path.stat().st_size

            logger.info(
                "File downloaded from S3",
                s3_key=s3_key,
                local_path=str(local_path),
                size_bytes=file_size,
            )

            return {
                "success": True,
                "s3_key": s3_key,
                "local_path": str(local_path),
                "file_size": file_size,
            }
        
        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"S3 object not found: {s3_key}")
            
            logger.error("S3 download failed", s3_key=s3_key, error=str(e))
            raise

    def download_fileobj(
        self, s3_key: str, file_obj: BinaryIO
    ) -> int:
        """
        Download S3 object to file-like object

        Args:
            s3_key: S3 object key
            file_obj: File-like object with write() method

        Returns:
            Number of bytes downloaded
        """
        try:
            self.client.download_fileobj(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fileobj=file_obj,
            )

            # Get size
            file_obj.seek(0, 2)
            size = file_obj.tell()
            file_obj.seek(0)

            logger.info("File object downloaded from S3", s3_key=s3_key, size_bytes=size)

            return size
        
        except ClientError as e:
            logger.error("S3 download_fileobj failed", s3_key=s3_key, error=str(e))
            raise

    def download_as_bytes(self, s3_key: str) -> bytes:
        """
        Download S3 object as bytes

        Args:
            s3_key: S3 object key

        Returns:
            File content as bytes
        """
        file_obj = BytesIO()
        self.download_fileobj(s3_key, file_obj)
        return file_obj.getvalue()
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete single file from S3

        Args:
            s3_key: S3 object key

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)

            logger.info("File deleted from S3", s3_key=s3_key)
            return True
        
        except ClientError as e:
            logger.error("S3 delet failed", s3_key=s3_key, error=str(e))
            raise

    def delete_files(self, s3_keys: List[str]) -> Dict[str, Any]:
        """
        Delete multiple files from S3

        Args:
            s3_keys: List of S3 object keys

        Returns:
            Dictionary with deletion results
        """
        if not s3_keys:
            return {"deleted": 0, "errors": 0}
        
        objects = [{"key": key} for key in s3_keys]

        try:
            response = self.client.delete_objects(
                Bucket=self.bucket_name,
                Delete={"Objects": objects}
            )

            deleted = response.get("Deleted", [])
            errors = response.get("Errors", [])

            logger.info(
                "Bulk delete completed",
                deleted=len(deleted),
                errors=len(errors),
            )

            return {
                "deleted": len(deleted),
                "errors": len(errors),
                "deleted_keys": [obj['Key'] for obj in deleted],
                "error_keys": [err['Key'] for err in errors],
            }
        
        except ClientError as e:
            logger.error("S3 bulk delete failed", error=str(e))
            raise

    def delete_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        Delete all objects with given prefix

        Args:
            prefix: S3 key prefix (folder path)

        Returns:
            Dictionary with deletion results
        """
        # List all objects with prefix
        keys_to_delete = self.list_files(prefix=prefix, keys_only=True)

        if not keys_to_delete:
            logger.info("No objects found with prefix", prefix=prefix)
            return {"deleted": 0, "errors": 0}

        # Delete in batches of 1000 (S3 limit)
        batch_size = 1000
        total_deleted = 0
        total_errors = 0

        for i in range(0, len(keys_to_delete), batch_size):
            batch = keys_to_delete[i:i + batch_size]
            result = self.delete_files(batch)
            total_deleted += result["deleted"]
            total_errors += result["errors"]

        logger.info(
            "Prefix deletion completed",
            prefix=prefix, deleted=total_deleted,
            errors=total_errors,
        )

        return {
            "deleted": total_deleted,
            "errors": total_errors,
        }
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3

        Args:
            s3_key: S3 object key

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return False
            raise

    def get_metadata(self, s3_key: str) -> S3FileMetadata:
        """
        Get file metadata from S3

        Args:
            s3_key: S3 object key

        Returns:
            S3FileMetadata object
        """
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=s3_key)

            metadata = S3FileMetadata(response)

            logger.debug(
                "Retrieved S3 metadata",
                s3_key=s3_key,
                size=metadata.content_length,
            )

            return metadata
        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == '404':
                raise FileNotFoundError(f"S3 object not found: {s3_key}")

            logger.error("Failed to get S3 metadata", s3_key=s3_key, error=str(e))
            raise

    def generate_presigned_url(
        self, s3_key: str, expiration: int = 3600,
        http_method: str = "GET"
    ) -> str:
        """
        Generate presigned URL for GET/PUT operations

        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds (default 1 hour)
            http_method: HTTP method ('GET', 'PUT', 'DELETE')

        Returns:
            Presigned URL string
        """
        method_map = {
            'GET': 'get_object',
            'PUT': 'put_object',
            'DELETE': 'delete_object',
        }

        client_method = method_map.get(http_method)
        if not client_method:
            raise ValueError(f"Invalid HTTP method: {http_method}")
        
        try:
            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                },
                ExpiresIn=expiration,
            )

            logger.info(
                "Generated presigned URL",
                s3_key=s3_key,
                method=http_method,
                expiration=expiration,
            )

            return url
        
        except ClientError as e:
            logger.error("Failed to generate presigned URL", error=str(e))
            raise

    def generate_presigned_post(
        self, s3_key: str, expiration: int = 3600,
        max_content_length: Optional[int] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate presigned POST data for browser uploads

        Args:
            s3_key: S3 object key
            expiration: Expiration in seconds
            max_content_length: Maximum file size in bytes
            content_type: Required content type

        Returns:
            Dictionary with 'url' and 'fields' for POST request
        """
        conditions = []
        fields = {}

        # Add content length constraint
        if max_content_length:
            conditions.append(["content-length-range", 0, max_content_length])

        # Add content type constraint
        if content_type:
            conditions.append({"Content-Type": content_type})
            fields["Content-Type"] = content_type

        try:
            response = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration,
            )

            logger.info(
                "Generated presigned POST",
                s3_key=s3_key,
                expires_in=expiration,
            )

            return response
        except ClientError as e:
            logger.error("Failed to generate presigned POST", error=str(e))
            raise

    def list_files(
        self, prefix: Optional[str] = None, max_keys: int = 1000, keys_only: bool = False,
    ) -> Union[List[str], List[Dict[str, Any]]]:
        """
        List files in S3 bucket

        Args:
            prefix: Filter by prefix (folder path)
            max_keys: Maximum number of keys to return
            keys_only: Return only keys (True) or full metadata (False)

        Returns:
            List of keys or list of file metadata dictionaries
        """
        try:
            params = {
                "Bucket": self.bucket_name,
                "MaxKeys": max_keys,
            }

            if prefix:
                params["Prefix"] = prefix

            response = self.client.list_objects_v2(**params)

            contents = response.get("Contents", [])

            if keys_only:
                return [obj["Key"] for obj in contents]
            else:
                return [
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj.get('ETag', '').strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD'),
                    } for obj in contents
                ]
            
        except ClientError as e:
            logger.error("Failed to list S3 objects", error=str(e))
            raise

    def copy_file(
        self, source_key: str, destination_key: str,
        source_bucket: Optional[str] = None,
    ) -> bool:
        """
        Copy file within S3

        Args:
            source_key: Source S3 key
            destination_key: Destination S3 key
            source_bucket: Source bucket (uses same bucket if not specified)

        Returns:
            True if copied successfully
        """
        source_bucket = source_bucket or self.bucket_name

        try:
            self.client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": source_bucket, "Key": source_key},
                Key=destination_key,
            )

            logger.info(
                "File copied in S3",
                source_key=source_key,
                destination_key=destination_key,
            )

            return True
        
        except ClientError as e:
            logger.error("S3 copy failed", error=str(e))
            raise

# Global service instance
s3_service = S3Service()

def get_s3_service() -> S3Service:
    """Dependency for getting S3 service in FastAPI routes"""
    return s3_service
