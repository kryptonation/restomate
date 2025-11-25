# S3 File Management Module - Setup Guide

## Overview

This module provides comprehensive S3 file management with:
- ✅ File upload with validation (size, type, MIME)
- ✅ Presigned URL generation
- ✅ File download (bytes and objects)
- ✅ Metadata management with JSON parsing
- ✅ Configurable naming conventions
- ✅ Date-based folder structures
- ✅ Server-side encryption
- ✅ File copying and soft/hard deletion

## Installation

### 1. Install Dependencies

```bash
pip install boto3 python-magic
```

### 2. Create Module Structure

```bash
mkdir -p app/modules/files
touch app/modules/files/__init__.py
```

### 3. Add Files to Module

Create these files in `app/modules/files/`:
- `models.py` - Database models
- `schemas.py` - Pydantic schemas
- `exceptions.py` - Custom exceptions
- `utils.py` - Validation and utilities
- `s3_service.py` - S3 operations
- `repository.py` - Database operations
- `services.py` - Business logic
- `router.py` - API endpoints

### 4. Update Configuration

Add S3 settings to `app/config.py` (see the config artifact).

### 5. Configure Environment

Add to `.env`:

```bash
# S3 Configuration
S3_BUCKET_NAME=my-app-bucket
S3_REGION=us-east-1
S3_MAX_FILE_SIZE_MB=100
S3_ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx,txt,csv,zip
S3_ALLOWED_MIME_TYPES=image/jpeg,image/png,image/gif,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/plain,text/csv,application/zip
S3_USE_UUID_PREFIX=true
S3_PRESERVE_FILENAME=true
S3_FOLDER_STRUCTURE={year}/{month}/{day}
S3_PRESIGNED_URL_EXPIRY=3600
S3_DOWNLOAD_URL_EXPIRY=300
S3_ENCRYPT_AT_REST=true
```

### 6. Create S3 Bucket

**AWS Console:**
1. Go to S3 Console
2. Click "Create bucket"
3. Enter bucket name (must be globally unique)
4. Select region
5. Configure settings:
   - Enable versioning (recommended)
   - Enable server-side encryption
   - Block public access (recommended)
6. Create bucket

**AWS CLI:**
```bash
aws s3 mb s3://my-app-bucket --region us-east-1
```

### 7. Create IAM Policy

Create policy with S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetObjectMetadata",
        "s3:HeadObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-app-bucket/*",
        "arn:aws:s3:::my-app-bucket"
      ]
    }
  ]
}
```

### 8. Create Database Migration

```bash
# Import models in alembic/env.py
from app.modules.files.models import FileUpload

# Create migration
alembic revision --autogenerate -m "Add files module"

# Review migration file
# Edit if needed

# Apply migration
alembic upgrade head
```

### 9. Register Router

In `app/main.py`:

```python
from app.modules.files.router import router as files_router

app.include_router(files_router, prefix=settings.api_v1_prefix)
```

## Usage Examples

### Upload File

```python
# Python
import httpx

async with httpx.AsyncClient() as client:
    files = {'file': open('document.pdf', 'rb')}
    data = {
        'folder': 'documents',
        'description': 'Important document',
        'is_public': False
    }
    
    response = await client.post(
        'http://localhost:8000/api/v1/files/upload',
        files=files,
        data=data,
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    file_data = response.json()
    print(f"File ID: {file_data['id']}")
    print(f"S3 Key: {file_data['s3_key']}")
```

```bash
# cURL
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "folder=documents" \
  -F "description=Important document"
```

### Get Presigned URL

```python
response = await client.get(
    f'http://localhost:8000/api/v1/files/{file_id}/presigned-url',
    params={'expiry': 3600, 'force_download': True},
    headers={'Authorization': f'Bearer {access_token}'}
)

url_data = response.json()
download_url = url_data['url']
```

### Download File

```python
# Download as streaming response
response = await client.get(
    f'http://localhost:8000/api/v1/files/{file_id}/download',
    params={'as_attachment': True},
    headers={'Authorization': f'Bearer {access_token}'}
)

with open('downloaded_file.pdf', 'wb') as f:
    f.write(response.content)
```

### Get File Metadata

```python
response = await client.get(
    f'http://localhost:8000/api/v1/files/{file_id}/metadata',
    headers={'Authorization': f'Bearer {access_token}'}
)

metadata = response.json()
print(f"Content Type: {metadata['content_type']}")
print(f"File Size: {metadata['file_size']} bytes")
print(f"Last Modified: {metadata['last_modified']}")
print(f"Custom Metadata: {metadata['metadata']}")
```

### Upload with Custom Metadata

```python
files = {'file': open('image.jpg', 'rb')}
data = {
    'folder': 'images',
    'metadata': json.dumps({
        'category': 'profile',
        'tags': ['user', 'avatar'],
        'processed': False
    })
}

response = await client.post(
    'http://localhost:8000/api/v1/files/upload',
    files=files,
    data=data,
    headers={'Authorization': f'Bearer {access_token}'}
)
```

## Configuration Options

### File Size Limits

Adjust `S3_MAX_FILE_SIZE_MB` in `.env`:

```bash
S3_MAX_FILE_SIZE_MB=50  # 50 MB limit
```

### Allowed File Types

Modify allowed extensions:

```bash
S3_ALLOWED_EXTENSIONS=jpg,png,pdf,docx
```

Modify allowed MIME types:

```bash
S3_ALLOWED_MIME_TYPES=image/jpeg,image/png,application/pdf
```

### Naming Conventions

**UUID Prefix (Recommended):**
```bash
S3_USE_UUID_PREFIX=true
S3_PRESERVE_FILENAME=true
# Result: 2025/01/15/uuid-4-here_document.pdf
```

**Timestamp Prefix:**
```bash
S3_USE_UUID_PREFIX=false
S3_PRESERVE_FILENAME=true
# Result: 2025/01/15/20250115_143022_document.pdf
```

**Original Filename Only:**
```bash
S3_USE_UUID_PREFIX=false
S3_PRESERVE_FILENAME=true
S3_FOLDER_STRUCTURE=
# Result: document.pdf (risky - no uniqueness guarantee)
```

### Folder Structures

Available placeholders: `{year}`, `{month}`, `{day}`, `{hour}`

```bash
# Date-based (default)
S3_FOLDER_STRUCTURE={year}/{month}/{day}
# Result: 2025/01/15/file.pdf

# Year-Month
S3_FOLDER_STRUCTURE=uploads/{year}-{month}
# Result: uploads/2025-01/file.pdf

# Custom
S3_FOLDER_STRUCTURE=documents/user-uploads
# Result: documents/user-uploads/file.pdf

# No structure (root)
S3_FOLDER_STRUCTURE=
# Result: file.pdf
```

## Security Best Practices

### 1. Bucket Security

- ✅ Enable versioning
- ✅ Enable server-side encryption
- ✅ Block public access (unless needed)
- ✅ Enable access logging
- ✅ Use bucket policies

### 2. IAM Permissions

- ✅ Use least privilege principle
- ✅ Separate read/write permissions
- ✅ Use IAM roles (not access keys) when possible

### 3. File Validation

The module validates:
- File size
- File extensions
- MIME types (detected from content)
- Filename sanitization

### 4. Access Control

- Files are private by default
- Set `is_public=true` only when necessary
- Use presigned URLs for temporary access
- Implement user-based access control

## Advanced Features

### Custom Folder per Upload

```python
files = {'file': open('report.pdf', 'rb')}
data = {'folder': f'users/{user_id}/documents'}

response = await client.post(
    'http://localhost:8000/api/v1/files/upload',
    files=files,
    data=data,
    headers={'Authorization': f'Bearer {access_token}'}
)
```

### File Copying

```python
response = await client.post(
    f'http://localhost:8000/api/v1/files/{file_id}/copy',
    json={
        'new_folder': 'archives',
        'new_metadata': {'archived': True, 'date': '2025-01-15'}
    },
    headers={'Authorization': f'Bearer {access_token}'}
)
```

### Soft Delete vs Hard Delete

```python
# Soft delete (keeps in S3, marks as deleted in DB)
await client.delete(
    f'http://localhost:8000/api/v1/files/{file_id}',
    headers={'Authorization': f'Bearer {access_token}'}
)

# Hard delete (removes from S3 and DB permanently)
await client.delete(
    f'http://localhost:8000/api/v1/files/{file_id}?hard_delete=true',
    headers={'Authorization': f'Bearer {access_token}'}
)
```

## Testing

### Unit Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_file(client: AsyncClient, auth_headers):
    files = {'file': ('test.pdf', b'fake pdf content', 'application/pdf')}
    
    response = await client.post(
        '/api/v1/files/upload',
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert 'id' in data
    assert 's3_key' in data
```

### LocalStack for Testing

Use LocalStack for local S3 testing:

```bash
# docker-compose.yml
services:
  localstack:
    image: localstack/localstack
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3
```

In `.env.test`:
```bash
S3_ENDPOINT_URL=http://localhost:4566
S3_BUCKET_NAME=test-bucket
```

## Troubleshooting

### Common Issues

**1. "NoSuchBucket" Error**
```bash
# Create bucket
aws s3 mb s3://my-app-bucket --region us-east-1
```

**2. "AccessDenied" Error**
- Check IAM permissions
- Verify bucket policy
- Ensure AWS credentials are correct

**3. "EntityTooLarge" Error**
- File exceeds S3 limit (5GB for single upload)
- Use multipart upload for large files

**4. MIME Type Detection Issues**
```bash
# Install python-magic
pip install python-magic

# On macOS, install libmagic
brew install libmagic
```

## Monitoring

### CloudWatch Metrics

Monitor S3 operations:
- Number of requests
- Bytes downloaded/uploaded
- Error rates
- Latency

### Application Logs

Check logs for:
```
s3_file_uploaded
s3_file_downloaded_bytes
s3_file_deleted
presigned_url_generated
```

## Performance Optimization

### 1. Use Presigned URLs

For frequent downloads, use presigned URLs instead of proxying through API:

```python
# Generate URL on server
url = await service.generate_presigned_url(file_id, expiry=3600)

# Client downloads directly from S3
response = requests.get(url)
```

### 2. Implement Caching

Cache file metadata:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_cached_metadata(file_id: int):
    return await service.get_file_metadata(file_id)
```

### 3. Use CloudFront CDN

For public files, use CloudFront for faster delivery.

## Next Steps

1. ✅ Set up S3 bucket and IAM permissions
2. ✅ Configure environment variables
3. ✅ Run database migrations
4. ✅ Test file upload/download
5. ⬜ Implement virus scanning (optional)
6. ⬜ Set up CloudFront CDN (optional)
7. ⬜ Configure lifecycle policies for old files
8. ⬜ Set up S3 event notifications (optional)

## Support

For issues or questions:
- Check AWS S3 documentation
- Review application logs
- Verify IAM permissions
- Test with LocalStack locally