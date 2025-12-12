# S3 File Management Service - Complete Guide

## Overview

Production-ready Amazon S3 file management service with:

✅ **File Upload** - From path, bytes, or file objects
✅ **File Download** - To path, bytes, or file objects  
✅ **Presigned URLs** - GET, PUT, POST for browser uploads
✅ **File Deletion** - Single, multiple, or by prefix
✅ **Metadata Operations** - Get full file metadata as JSON
✅ **File Listing** - With prefix filtering
✅ **File Copy** - Within or between buckets
✅ **Existence Checking** - Fast head_object calls
✅ **Auto Content-Type** - MIME detection
✅ **Server-Side Encryption** - AES256 by default
✅ **Object Tagging** - For categorization
✅ **Storage Classes** - STANDARD, INTELLIGENT_TIERING, etc.

## Configuration

### 1. Environment Variables

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1

# S3 Configuration
S3_BUCKET_NAME=your-bucket-name
```

### 2. Update core/config.py

```python
class Settings(BaseSettings):
    # AWS Settings
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "ap-south-1"
    
    # S3 Settings
    s3_bucket_name: str
```

### 3. Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://your-bucket-name --region ap-south-1

# Enable versioning (optional)
aws s3api put-bucket-versioning \
    --bucket your-bucket-name \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket your-bucket-name \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
```

## Usage Examples

### Example 1: Upload Local File

```python
from src.common.s3_service import s3_service

# Simple upload
result = s3_service.upload_file(
    file_path="path/to/menu-item.jpg",
    prefix="restaurants/rest-123/menu"
)

print(f"Uploaded to: {result['s3_url']}")
print(f"HTTPS URL: {result['https_url']}")
print(f"File size: {result['file_size']} bytes")
```

### Example 2: Upload with Custom Settings

```python
# Upload with metadata, tags, and storage class
result = s3_service.upload_file(
    file_path="path/to/document.pdf",
    s3_key="documents/licenses/restaurant-123-license.pdf",
    content_type="application/pdf",
    metadata={
        "restaurant_id": "123",
        "document_type": "license",
        "uploaded_by": "admin@restaurant.com"
    },
    tags={
        "Department": "Legal",
        "Type": "License",
        "Retention": "7years"
    },
    storage_class="STANDARD_IA",  # Infrequent Access
    acl="private",
    server_side_encryption=True
)
```

### Example 3: Upload Bytes Content

```python
# Upload from bytes (e.g., generated image, PDF)
import io
from PIL import Image

# Create image
img = Image.new('RGB', (100, 100), color='red')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes = img_bytes.getvalue()

# Upload
result = s3_service.upload_bytes(
    content=img_bytes,
    s3_key="generated/test-image.png",
    content_type="image/png"
)
```

### Example 4: Upload File Object (FastAPI)

```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_menu_image(file: UploadFile = File(...)):
    """Upload menu image from FastAPI"""
    
    # Upload directly from UploadFile
    result = s3_service.upload_fileobj(
        file_obj=file.file,
        s3_key=f"menus/{file.filename}",
        content_type=file.content_type
    )
    
    return {"success": True, "s3_url": result['s3_url']}
```

### Example 5: Download File

```python
# Download to local path
result = s3_service.download_file(
    s3_key="restaurants/rest-123/menu/pizza.jpg",
    local_path="downloads/pizza.jpg"
)

print(f"Downloaded {result['file_size']} bytes")
```

### Example 6: Download as Bytes

```python
# Download file content as bytes
file_bytes = s3_service.download_as_bytes(
    s3_key="documents/invoice-001.pdf"
)

# Use bytes content
print(f"Downloaded {len(file_bytes)} bytes")

# Or serve via FastAPI
from fastapi.responses import Response

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    s3_key = f"invoices/{file_id}.pdf"
    file_bytes = s3_service.download_as_bytes(s3_key)
    
    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice-{file_id}.pdf"
        }
    )
```

### Example 7: Generate Presigned URL (Download)

```python
# Generate URL for direct download (valid for 1 hour)
url = s3_service.generate_presigned_url(
    s3_key="restaurants/rest-123/menu/pizza.jpg",
    expiration=3600,  # 1 hour
    http_method='GET'
)

# Share URL with user
print(f"Download link (valid 1 hour): {url}")

# User can download without AWS credentials
# curl "{url}" -o pizza.jpg
```

### Example 8: Generate Presigned URL (Upload)

```python
# Generate URL for direct upload from browser
url = s3_service.generate_presigned_url(
    s3_key="uploads/user-123/profile.jpg",
    expiration=1800,  # 30 minutes
    http_method='PUT'
)

# Frontend can upload directly
"""
// JavaScript
const file = document.getElementById('fileInput').files[0];

fetch(presignedUrl, {
    method: 'PUT',
    body: file,
    headers: {
        'Content-Type': file.type
    }
})
.then(response => console.log('Uploaded!'))
.catch(error => console.error('Upload failed:', error));
"""
```

### Example 9: Generate Presigned POST (Browser Upload)

```python
# Better for browser uploads with form data
post_data = s3_service.generate_presigned_post(
    s3_key="uploads/${filename}",  # ${filename} will be replaced
    expiration=1800,  # 30 minutes
    max_content_length=10 * 1024 * 1024,  # 10 MB max
    content_type="image/jpeg"
)

# Returns: {'url': '...', 'fields': {...}}

# Frontend HTML form
"""
<form action="{post_data['url']}" method="post" enctype="multipart/form-data">
    <!-- Hidden fields from post_data['fields'] -->
    {% for key, value in post_data['fields'].items() %}
    <input type="hidden" name="{{ key }}" value="{{ value }}">
    {% endfor %}
    
    <input type="file" name="file" required>
    <button type="submit">Upload</button>
</form>
"""
```

### Example 10: Get File Metadata

```python
# Get comprehensive metadata
metadata = s3_service.get_metadata(
    s3_key="documents/contract-001.pdf"
)

# Access metadata
print(metadata.to_dict())
"""
{
    'content_type': 'application/pdf',
    'content_length': 245760,
    'content_length_mb': 0.23,
    'last_modified': '2024-12-10T10:30:00+00:00',
    'etag': 'abc123...',
    'metadata': {'document_type': 'contract'},
    'storage_class': 'STANDARD',
    'server_side_encryption': 'AES256',
    'version_id': 'v123'
}
"""
```

### Example 11: Check File Existence

```python
# Fast check without downloading
if s3_service.file_exists("path/to/file.jpg"):
    print("File exists in S3")
else:
    print("File not found")
```

### Example 12: Delete Files

```python
# Delete single file
s3_service.delete_file("old/file.jpg")

# Delete multiple files
result = s3_service.delete_files([
    "temp/file1.jpg",
    "temp/file2.jpg",
    "temp/file3.jpg"
])

print(f"Deleted: {result['deleted']}")
print(f"Errors: {result['errors']}")

# Delete entire folder (prefix)
result = s3_service.delete_prefix("temp/old-uploads/")
print(f"Deleted {result['deleted']} files")
```

### Example 13: List Files

```python
# List all files in folder
files = s3_service.list_files(
    prefix="restaurants/rest-123/",
    max_keys=100
)

for file in files:
    print(f"{file['key']} - {file['size']} bytes")

# Get only keys (faster)
keys = s3_service.list_files(
    prefix="menus/",
    keys_only=True
)
print(f"Found {len(keys)} menu images")
```

### Example 14: Copy Files

```python
# Copy file within same bucket
s3_service.copy_file(
    source_key="uploads/temp/image.jpg",
    destination_key="restaurants/rest-123/menu/image.jpg"
)

# Copy from another bucket
s3_service.copy_file(
    source_key="backup/image.jpg",
    destination_key="active/image.jpg",
    source_bucket="my-backup-bucket"
)
```

## Integration Examples

### 1. Restaurant Profile Image Upload

```python
# services/restaurant_service.py

from src.common.s3_service import s3_service
from src.common.file_validator import file_validator, FileCategory

class RestaurantService:
    async def upload_profile_image(
        self,
        restaurant_id: UUID,
        image_file: UploadFile,
    ):
        """Upload and set restaurant profile image"""
        
        # Validate file
        validation = file_validator.validate_fastapi_upload(
            file=image_file,
            category=FileCategory.IMAGE
        )
        
        if not validation.is_valid:
            raise InvalidFileTypeError("Invalid image", validation.errors)
        
        # Generate S3 key
        s3_key = f"restaurants/{restaurant_id}/profile.jpg"
        
        # Upload to S3
        result = s3_service.upload_fileobj(
            file_obj=image_file.file,
            s3_key=s3_key,
            content_type=image_file.content_type,
            metadata={
                "restaurant_id": str(restaurant_id),
                "upload_date": datetime.now().isoformat()
            },
            tags={
                "Type": "ProfileImage",
                "RestaurantID": str(restaurant_id)
            }
        )
        
        # Generate public URL (1 year expiry for profile images)
        public_url = s3_service.generate_presigned_url(
            s3_key=s3_key,
            expiration=365 * 24 * 3600  # 1 year
        )
        
        # Update database
        await self.repository.update(
            restaurant_id,
            {"profile_image_url": public_url, "profile_image_s3_key": s3_key}
        )
        
        return {
            "image_url": public_url,
            "s3_key": s3_key
        }
```

### 2. Menu PDF Generation and Upload

```python
# services/menu_service.py

from reportlab.pdfgen import canvas
from io import BytesIO

class MenuService:
    async def generate_and_upload_menu_pdf(
        self,
        restaurant_id: UUID,
        menu_items: List[Dict]
    ):
        """Generate menu PDF and upload to S3"""
        
        # Generate PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        
        # Add content
        pdf.drawString(100, 750, f"Restaurant Menu")
        y = 700
        for item in menu_items:
            pdf.drawString(100, y, f"{item['name']} - ₹{item['price']}")
            y -= 20
        
        pdf.save()
        pdf_bytes = buffer.getvalue()
        
        # Upload to S3
        s3_key = f"restaurants/{restaurant_id}/menu.pdf"
        result = s3_service.upload_bytes(
            content=pdf_bytes,
            s3_key=s3_key,
            content_type="application/pdf",
            metadata={
                "restaurant_id": str(restaurant_id),
                "generated_at": datetime.now().isoformat(),
                "items_count": str(len(menu_items))
            }
        )
        
        # Generate download URL
        download_url = s3_service.generate_presigned_url(
            s3_key=s3_key,
            expiration=7 * 24 * 3600  # 1 week
        )
        
        return {
            "pdf_url": download_url,
            "s3_key": s3_key,
            "file_size": len(pdf_bytes)
        }
```

### 3. Direct Browser Upload Endpoint

```python
# routers/upload.py

@router.post("/get-upload-url")
async def get_upload_url(
    filename: str,
    content_type: str,
    restaurant_id: str = None,
):
    """Get presigned URL for direct browser upload"""
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if content_type not in allowed_types:
        raise HTTPException(400, "Invalid file type")
    
    # Generate unique S3 key
    file_ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    s3_key = f"uploads/{restaurant_id}/{unique_filename}"
    
    # Generate presigned POST
    post_data = s3_service.generate_presigned_post(
        s3_key=s3_key,
        expiration=1800,  # 30 minutes
        max_content_length=10 * 1024 * 1024,  # 10 MB
        content_type=content_type
    )
    
    return {
        "upload_url": post_data['url'],
        "fields": post_data['fields'],
        "s3_key": s3_key,
        "expires_in": 1800
    }
```

### 4. Download Invoice with Metadata

```python
# services/invoice_service.py

class InvoiceService:
    async def download_invoice(
        self,
        invoice_id: UUID,
        user_id: UUID
    ):
        """Download invoice with access control"""
        
        # Verify access
        invoice = await self.repository.get(invoice_id)
        if invoice.user_id != user_id:
            raise PermissionError("Access denied")
        
        # Get S3 key from database
        s3_key = invoice.s3_key
        
        # Get metadata
        metadata = s3_service.get_metadata(s3_key)
        
        # Download file
        file_bytes = s3_service.download_as_bytes(s3_key)
        
        return {
            "content": file_bytes,
            "filename": f"invoice-{invoice.invoice_number}.pdf",
            "content_type": metadata.content_type,
            "size": metadata.content_length,
            "generated_date": invoice.created_at
        }
```

### 5. Bulk Image Upload

```python
@router.post("/gallery/bulk-upload")
async def bulk_upload_gallery(
    files: List[UploadFile] = File(...),
    restaurant_id: str = None,
):
    """Upload multiple images to gallery"""
    
    results = []
    errors = []
    
    for file in files:
        try:
            # Validate
            validation = file_validator.validate_fastapi_upload(
                file=file,
                category=FileCategory.IMAGE
            )
            
            if not validation.is_valid:
                errors.append({
                    "filename": file.filename,
                    "errors": validation.errors
                })
                continue
            
            # Upload
            s3_key = f"restaurants/{restaurant_id}/gallery/{file.filename}"
            result = s3_service.upload_fileobj(
                file_obj=file.file,
                s3_key=s3_key,
                content_type=file.content_type
            )
            
            # Generate URL
            url = s3_service.generate_presigned_url(s3_key, expiration=31536000)
            
            results.append({
                "filename": file.filename,
                "url": url,
                "s3_key": s3_key,
                "size": result['file_size']
            })
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "uploaded": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }
```

## Best Practices

### 1. Organize S3 Keys

```python
# Good key structure
restaurants/{restaurant_id}/profile.jpg
restaurants/{restaurant_id}/menu/{item_id}.jpg
restaurants/{restaurant_id}/documents/{type}/{filename}
users/{user_id}/uploads/{timestamp}_{filename}

# Use prefixes for easy management
production/
staging/
backups/
temp/
```

### 2. Set Appropriate Expiration Times

```python
# Profile images - 1 year (rarely change)
profile_url = generate_presigned_url(key, expiration=365*24*3600)

# Temporary uploads - 1 hour
temp_url = generate_presigned_url(key, expiration=3600)

# Invoice downloads - 7 days
invoice_url = generate_presigned_url(key, expiration=7*24*3600)
```

### 3. Use Metadata for Tracking

```python
s3_service.upload_file(
    file_path=path,
    s3_key=key,
    metadata={
        "uploaded_by": user_id,
        "upload_timestamp": datetime.now().isoformat(),
        "original_filename": original_name,
        "content_hash": file_hash,
        "restaurant_id": restaurant_id
    }
)
```

### 4. Implement Lifecycle Policies

```python
# Configure via AWS CLI or Console
# Delete temp uploads after 7 days
# Transition to Glacier after 90 days
# Delete old backups after 365 days
```

### 5. Error Handling

```python
from botocore.exceptions import ClientError

try:
    result = s3_service.upload_file(path, key)
except FileNotFoundError:
    # Handle missing local file
    pass
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchBucket':
        # Bucket doesn't exist
        pass
    elif error_code == 'AccessDenied':
        # Permission issue
        pass
except Exception as e:
    # Handle other errors
    logger.error("Upload failed", error=str(e))
```

## Production Checklist

- [ ] S3 bucket created with proper naming
- [ ] Bucket versioning enabled
- [ ] Server-side encryption enabled
- [ ] Lifecycle policies configured
- [ ] IAM user/role with minimal permissions
- [ ] CORS configuration (if browser uploads)
- [ ] CloudFront CDN setup (optional)
- [ ] Backup strategy implemented
- [ ] Monitoring and alerts configured
- [ ] Cost optimization reviewed
- [ ] Access logging enabled
- [ ] Object tagging strategy defined
- [ ] Presigned URL security reviewed
- [ ] File validation integrated
- [ ] Error handling implemented

This S3 service provides enterprise-grade file management with security, performance, and maintainability built-in!