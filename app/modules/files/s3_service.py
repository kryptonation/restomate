# app/modules/files/s3_service.py

import io
from typing import Optional, Dict, Any, BinaryIO

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from app.config import settings
from app.core.logging import get_logger
from app.modules.files.exceptions import S3OperationException
from app.modules.files.utils import metadata_parser

logger = get_logger(__name__)


class S3Service:
    """Service for S3 Operations."""

    def __init__(self):
        # Configure boto3 client
        config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"}
        )

        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
            config=config
        )

        self.bucket_name = settings.s3_bucket_name
        self.region = settings.s3_effective_region

    async def upload_file(
        self, file_contents: bytes, s3_key: str, content_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """
        Upload a file to S3

        Args:
            file_content: File content as bytes
            s3_key: S3 object key
            content_type: MIME type
            metadata: Optional metadata dictionary
            is_public: Wether file should be publicly accessible

        Returns:
            Dict with upload response including ETag
        """
        try:
            # Prepare metadata
            s3_metadata = metadata_parser.prepare_metadata_for_s3(metadata)

            # Upload parameters
            upload_params = {
                "Bucket": self.bucket_name,
                "Key": s3_key,
                "Body": file_contents,
                "ContentType": content_type,
                "Metadata": s3_metadata
            }

            # Add ACL if public
            if is_public:
                upload_params["ACL"] = "public-read"

            # Add server-side encryption
            if settings.s3_encrypt_at_rest:
                upload_params["ServerSideEncryption"] = "AES256"

            # Upload to S3
            response = self.client.put_object(**upload_params)

            logger.info(
                "s3_file_uploaded",
                s3_key=s3_key,
                bucket=self.bucket_name,
                size=len(file_contents),
                etag=response.get("ETag")
            )

            return {
                "etag": response.get("ETag", "").strip('"'),
                "version_id": response.get("VersionId"),
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "region": self.region
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error("s3_upload_error", s3_key=s3_key, error=str(e), code=error_code)
            raise S3OperationException("upload", str(e)) from e
        except Exception as e:
            logger.error("s3_upload_error", s3_key=s3_key, error=str(e))
            raise S3OperationException("upload", str(e)) from e
        
    async def generate_presigned_url(
        self, s3_key: str, expiry: Optional[int] = None,
        response_content_type: Optional[str] = None,
        response_content_disposition: Optional[str] = None
    ) -> str:
        """
        Generate presigned URL for S3 object.

        Args:
            s3_key: S3 object key
            expiry: URL expiry in seconds
            response_content_type: Override content type in response
            response_content_disposition: Set content disposition (e.g., for downloads)

        Returns:
            Presigned URL string
        """
        try:
            expiry = expiry or settings.s3_presigned_url_expiry

            params = {
                "Bucket": self.bucket_name,
                "Key": s3_key
            }

            # Add response overrides
            response_params = {}
            if response_content_type:
                response_params["ResponseContentType"] = response_content_type
            if response_content_disposition:
                response_params["ResponseContentDisposition"] = response_content_disposition

            if response_params:
                params["ResponseContentType"] = response_content_type
                params["ResponseContentDisposition"] = response_content_disposition

            url = self.client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expiry
            )

            logger.info("presigned_url_generated", s3_key=s3_key, expiry=expiry)

            return url
        
        except ClientError as e:
            logger.error("presigned_url_error", s3_key=s3_key, error=str(e))
            raise S3OperationException("generate_presigned_url", str(e)) from e
        
    async def get_object_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get metadata for S3 object.

        Args:
            s3_key: S3 object key

        Returns:
            Dict with object metadata
        """
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            # Parse metadata
            metadata = metadata_parser.parse_metadata(response.get("Metadata", {}))

            result = {
                "s3_key": s3_key,
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag", "").strip('"'),
                "metadata": metadata,
                "storage_class": response.get("StorageClass"),
                "server_side_encryption": response.get("ServerSideEncryption"),
                "version_id": response.get("VersionId")
            }

            logger.info("s3_metadata_retrieved", s3_key=s3_key)

            return result
        
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.warning("s3_object_not_found", s3_key=s3_key)
                raise S3OperationException("get_metadata", "Object not found") from e
            logger.error("s3_metadata_error", s3_key=s3_key, error=str(e))
            raise S3OperationException("get_metadata", str(e)) from e

    async def download_file_as_bytes(self, s3_key: str) -> bytes:
        """
        Download file from s3 as bytes.

        Args:
            s3_key: S3 object key

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            content = response["Body"].read()

            logger.info(
                "s3_file_downloaded_bytes",
                s3_key=s3_key,
                size=len(content)
            )

            return content
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning("s3_object_not_found", s3_key=s3_key)
                raise S3OperationException("download", f"Object not found: {s3_key}") from e
            logger.error("s3_download_error", s3_key=s3_key, error=str(e))
            raise S3OperationException("download", str(e)) from e
        
    async def download_file_as_object(self, s3_key: str) -> BinaryIO:
        """
        Download file from S3 as file-like object.

        Args:
            s3_key: S3 object key

        Returns:
            BytesIO object containing file content
        """
        try:
            content = await self.download_file_as_bytes(s3_key)
            file_obj = io.BytesIO(content)

            logger.info("s3_file_downloaded_object", s3_key=s3_key)

            return file_obj
        except Exception as e:
            logger.error("s3_download_object_error", s3_key=s3_key, error=str(e))
            raise

    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            logger.info("s3_file_deleted", s3_key=s3_key)

            return True
        except ClientError as e:
            logger.error("s3_delete_error", s3_key=s3_key, error=str(e))
            raise S3OperationException("delete", str(e)) from e
        
    async def check_object_exists(self, s3_key: str) -> bool:
        """
        Check if object exists in S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise S3OperationException("check_exists", str(e)) from e
        
    async def copy_file(
        self, source_key: str, destination_key: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Copy file within S3.

        Args:
            source_key: Source S3 key
            destination_key: Destination S3 key
            metadata: Optional new metadata

        Returns:
            Dict with copy response
        """
        try:
            copy_source = {
                "Bucket": self.bucket_name,
                "Key": source_key
            }

            copy_params = {
                "CopySource": copy_source,
                "Bucket": self.bucket_name,
                "Key": destination_key
            }

            if metadata:
                copy_params["Metadata"] = metadata_parser.prepare_metadata_for_s3(metadata)
                copy_params["MetadataDirective"] = "REPLACE"

            response = self.client.copy_object(**copy_params)

            logger.info("s3_file_copied", source=source_key, destination=destination_key)

            return {
                "etag": response.get("CopyObjectResult", {}).get("ETag", "").strip('"'),
                "destination_key": destination_key
            }
        
        except ClientError as e:
            logger.error("s3_copy_error", source=source_key, error=str(e))
            raise S3OperationException("copy", str(e)) from e
        

s3_service = S3Service()
