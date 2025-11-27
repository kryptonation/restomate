# app/modules/files/router.py

from typing import Optional

from fastapi import (
    APIRouter, Depends, UploadFile, File, status, Query,
    Response
)
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.dependencies import ActiveUser, require_permission
from app.modules.files.services import FileService
from app.modules.files.schemas import (
    FileUploadResponse, PresignedUrlResponse, FileMetadataResponse,
    FileListResponse
)

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(db=Depends(get_db), user=Depends(ActiveUser)):
    """Dependency to get file service."""
    return FileService(db=db)


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    file: UploadFile = File(...),
    folder: Optional[str] = None,
    description: Optional[str] = None,
    is_public: bool = False,
    _: None = Depends(require_permission("files", "create"))
):
    """
    Upload a file to S3

    - **file**: File to upload
    - **folder**: Optional folder path in S3
    - **description**: Optional file description
    - **is_public**: Whether file should be publicly accessible
    """
    content = await file.read()

    # Upload file
    file_upload = await service.upload_file(
        file_content=content,
        filename=file.filename,
        content_type=file.content_type,
        folder=folder,
        description=description,
        is_public=is_public,
        uploaded_by_id=current_user.id
    )

    return file_upload


@router.get("/", response_model=FileListResponse)
async def list_files(
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    content_type: Optional[str] = None,
    _: None = Depends(require_permission("files", "read"))
):
    """
    List uploaded files with pagination.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **content_type**: Filter by content type (e.g., 'Image', 'application/pdf')
    """
    files, total = await service.list_files(
        skip=skip,
        limit=limit,
        uploaded_by_id=current_user.id,
        content_type=content_type
    )

    return {
        "files": files,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit
    }


@router.get("/{file_id}", response_model=FileUploadResponse)
async def get_file(
    file_id: int,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    _: None = Depends(require_permission("files", "read"))
):
    """
    Get file details by ID.
    """
    file_upload = await service.get_file(file_id=file_id)
    return file_upload


@router.get("/{file_id}/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(
    file_id: int,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    expiry: Optional[int] = Query(None, description="URL expiry in seconds"),
    force_download: bool = Query(False, description="Force file download"),
    _: None = Depends(require_permission("files", "read"))
):
    """
    Generate presigned URL for file access.

    - **file_id**: File ID
    - **expiry**: URL expiry in seconds (default from settings)
    - **force_download**: If true, browser will download instead of display
    """
    file_upload = await service.get_file(file_id=file_id)

    url = await service.generate_presigned_url(
        file_id=file_id,
        expiry=expiry,
        force_download=force_download
    )

    from app.config import settings

    return {
        "url": url,
        "expires_in": expiry or settings.s3_presigned_url_expiry,
        "s3_key": file_upload.s3_key,
        "original_filename": file_upload.original_filename
    }


@router.get("/{file_id}/metadata", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: int,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    _: None = Depends(require_permission("files", "read"))
):
    """
    Get detailed file metadata from S3.
    """
    metadata = await service.get_file_metadata(file_id=file_id)

    return {
        "s3_key": metadata["s3_key"],
        "original_filename": metadata["original_filename"],
        "content_type": metadata["content_type"],
        "file_size": metadata["file_size"],
        "last_modified": metadata["s3_last_modified"],
        "etag": metadata["s3_etag"],
        "metadata": metadata["s3_metadata"],
        "storage_class": metadata["storage_class"]
    }


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    as_attachment: bool = Query(True, description="Download as attachment"),
    _: None = Depends(require_permission("files", "read"))
):
    """
    Download file as bytes.

    - **file_id**: File ID
    - **as_attachment**: If true, download as attachment; if false, display inline
    """
    file_obj, file_upload = await service.download_file_as_object(file_id=file_id)

    # Set content disposition
    content_disposition_type = "attachment" if as_attachment else "inline"
    content_disposition = f"{content_disposition_type}; filename='{file_upload.original_filename}'"

    return StreamingResponse(
        file_obj,
        media_type=file_upload.content_type,
        headers={
            "Content-Disposition": content_disposition,
            "Content-Length": str(file_upload.file_size)
        }
    )


@router.get("/{file_id}/download-bytes")
async def download_file_bytes(
    file_id: int,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    _: None = Depends(require_permission("files", "read"))
):
    """
    Download file as raw bytes.
    """
    content, file_upload = await service.download_file_as_bytes(file_id=file_id)

    return Response(
        content=content,
        media_type=file_upload.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_upload.original_filename}"',
            "Content-Length": str(len(content))
        }
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    hard_delete: bool = Query(False, description="Permanently delete from S3"),
    _: None = Depends(require_permission("files", "delete"))
):
    """
    Delete file.

    - **file_id**: File ID
    - **hard_delete**: If true, permanently delete from S3; if false, soft delete
    """
    await service.delete_file(file_id=file_id, hard_delete=hard_delete)


@router.put("/{file_id}/metadata", response_model=FileUploadResponse)
async def upload_file_metadata(
    file_id: int,
    metadata: dict,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    description: Optional[str] = None,
    _: None = Depends(require_permission("files", "update"))
):
    """
    Update file metadata.

    - **file_id**: File ID
    - **metadata**: New metadata dictionary
    - **description**: New description
    """
    file_upload = await service.update_file_metadata(
        file_id=file_id,
        metadata=metadata,
        description=description
    )

    return file_upload


@router.post("/{file_id}/copy", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def copy_file(
    file_id: int,
    current_user: ActiveUser,
    service: FileService = Depends(get_file_service),
    new_folder: Optional[str] = None,
    new_metadata: Optional[dict] = None,
    _: None = Depends(require_permission("files", "create"))
):
    """
    Copy file to new location.

    - **file_id**: Source file ID
    - **new_folder**: New folder path
    - **new_metadata**: New metadata for copied file
    """
    new_file = await service.copy_file(
        file_id=file_id,
        new_folder=new_folder,
        new_metadata=new_metadata,
    )

    return new_file

