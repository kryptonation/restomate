# File Validation Utility - Complete Implementation Guide

## Overview

This is a production-ready file validation utility with:

- ✅ File size validation with configurable limits
- ✅ Extension-based validation
- ✅ MIME type detection (extension + content-based)
- ✅ Magic number verification for security
- ✅ Image dimension validation
- ✅ Dangerous content detection
- ✅ File hash calculation
- ✅ Category-based validation
- ✅ Centralized configuration from settings
- ✅ FastAPI integration support
- ✅ Comprehensive error reporting
- ✅ Security checks for executable files

## Features

### Multi-Layer Validation

1. **Extension Validation** - Checks file extension against whitelist
2. **MIME Type Detection** - Uses multiple methods (mimetypes, magic numbers, imghdr)
3. **Content Verification** - Validates actual file content matches extension
4. **Size Limits** - Enforces min/max file size constraints
5. **Security Checks** - Detects dangerous extensions and content
6. **Image Validation** - Verifies dimensions and format
7. **Hash Calculation** - Generates SHA256 for deduplication

## File Categories

Pre-configured validation for common use cases:

| Category | Extensions | Max Size | Use Case |
|----------|-----------|----------|----------|
| **IMAGE** | jpg, png, gif, webp, svg | 10 MB | Menu photos, profiles, restaurant images |
| **DOCUMENT** | pdf, doc, docx, txt | 20 MB | Licenses, contracts, reports |
| **SPREADSHEET** | xls, xlsx, csv | 15 MB | Inventory, analytics, bulk data |
| **VIDEO** | mp4, avi, mov, webm | 100 MB | Promotional videos, tutorials |
| **AUDIO** | mp3, wav, ogg | 20 MB | Promotional audio |
| **ARCHIVE** | zip, tar, gz, rar | 50 MB | Bulk uploads, backups |

## Configuration

### 1. Application Settings

Update your `.env` file:

```bash
# File Upload Configuration
MAX_UPLOAD_SIZE=10485760  # 10 MB in bytes
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf,docx,xlsx

# Upload Directory
UPLOAD_DIR=uploads
```

### 2. Update core/config.py

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # File Upload Settings
    max_upload_size: int = 10485760  # 10 MB
    upload_dir: str = "uploads"
    allowed_extensions: str = "jpg,jpeg,png,gif,pdf,docx,xlsx"
```

### 3. Custom Category Configuration

```python
from src.common.file_validator import FileValidator, FileCategory, FileValidationConfig

# Create custom validator with specific rules
custom_configs = {
    FileCategory.IMAGE: FileValidationConfig(
        category=FileCategory.IMAGE,
        allowed_extensions={'.jpg', '.png', '.webp'},
        allowed_mime_types={'image/jpeg', 'image/png', 'image/webp'},
        max_size_bytes=5 * 1024 * 1024,  # 5 MB
        min_size_bytes=1024,  # 1 KB minimum
        check_content=True,
        description="Restaurant menu images"
    )
}

validator = FileValidator(custom_configs=custom_configs)
```

## Usage Examples

### Example 1: Validate Local File

```python
from pathlib import Path
from src.common.file_validator import file_validator, FileCategory

# Validate an image file
result = file_validator.validate_file(
    file_path="path/to/menu-item.jpg",
    category=FileCategory.IMAGE
)

if result.is_valid:
    print(f"✓ Valid file: {result.file_name}")
    print(f"  Size: {result.file_size / 1024:.2f} KB")
    print(f"  MIME: {result.detected_mime_type}")
else:
    print(f"✗ Invalid file: {result.file_name}")
    for error in result.errors:
        print(f"  - {error}")

# Check warnings
if result.warnings:
    print("Warnings:")
    for warning in result.warnings:
        print(f"  ! {warning}")
```

### Example 2: Validate with Image Dimensions

```python
# Validate image with dimension constraints
result = file_validator.validate_file(
    file_path="path/to/restaurant-banner.jpg",
    category=FileCategory.IMAGE,
    check_dimensions=True,
    max_width=1920,
    max_height=1080
)

if result.is_valid:
    print(f"Image dimensions: {result.metadata.get('width')}x{result.metadata.get('height')}")
    print(f"Format: {result.metadata.get('format')}")
```

### Example 3: Validate Uploaded File with Hash

```python
# Calculate hash for deduplication
result = file_validator.validate_file(
    file_path="path/to/document.pdf",
    category=FileCategory.DOCUMENT,
    calculate_hash=True
)

if result.is_valid:
    print(f"File hash: {result.metadata.get('sha256')}")
    # Use hash to check for duplicates
```

### Example 4: Validate Upload Content (bytes)

```python
# When you have file content as bytes
with open("path/to/file.jpg", "rb") as f:
    file_content = f.read()

result = file_validator.validate_upload(
    file_content=file_content,
    filename="menu-photo.jpg",
    category=FileCategory.IMAGE,
    save_to=Path("uploads/menus/menu-photo.jpg")
)

if result.is_valid:
    print(f"File saved to: {result.file_path}")
```

### Example 5: FastAPI Integration

```python
# app/routers/upload.py

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from src.common.file_validator import file_validator, FileCategory

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/menu-image")
async def upload_menu_image(
    file: UploadFile = File(...),
    restaurant_id: str = None,
):
    """Upload restaurant menu image"""
    
    # Validate uploaded file
    result = file_validator.validate_fastapi_upload(
        file=file,
        category=FileCategory.IMAGE,
        save_to=Path(f"uploads/restaurants/{restaurant_id}/menu/{file.filename}")
    )
    
    # Check validation result
    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "File validation failed",
                "errors": result.errors,
                "warnings": result.warnings
            }
        )
    
    # File is valid and saved
    return {
        "success": True,
        "file_name": result.file_name,
        "file_size": result.file_size,
        "file_path": result.file_path,
        "mime_type": result.detected_mime_type,
        "metadata": result.metadata
    }

@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "license",
):
    """Upload restaurant document (license, permit, etc.)"""
    
    result = file_validator.validate_fastapi_upload(
        file=file,
        category=FileCategory.DOCUMENT,
        save_to=Path(f"uploads/documents/{document_type}/{file.filename}")
    )
    
    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Document validation failed",
                "errors": result.errors
            }
        )
    
    return {
        "success": True,
        "document_id": str(uuid.uuid4()),
        "file_info": result.to_dict()
    }

@router.post("/bulk-upload")
async def upload_bulk_menu_items(
    file: UploadFile = File(...),
):
    """Upload CSV/Excel file for bulk menu import"""
    
    result = file_validator.validate_fastapi_upload(
        file=file,
        category=FileCategory.SPREADSHEET,
    )
    
    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid file", "errors": result.errors}
        )
    
    # Process spreadsheet (parse CSV/Excel)
    # ... processing logic ...
    
    return {
        "success": True,
        "items_imported": 42,
        "file_info": result.to_dict()
    }
```

### Example 6: Multiple File Upload

```python
@router.post("/gallery")
async def upload_restaurant_gallery(
    files: List[UploadFile] = File(...),
    restaurant_id: str = None,
):
    """Upload multiple images to restaurant gallery"""
    
    results = []
    errors = []
    
    for file in files:
        try:
            result = file_validator.validate_fastapi_upload(
                file=file,
                category=FileCategory.IMAGE,
                save_to=Path(f"uploads/restaurants/{restaurant_id}/gallery/{file.filename}")
            )
            
            if result.is_valid:
                results.append({
                    "file_name": result.file_name,
                    "file_path": result.file_path,
                    "status": "success"
                })
            else:
                errors.append({
                    "file_name": file.filename,
                    "errors": result.errors,
                    "status": "failed"
                })
        
        except Exception as e:
            errors.append({
                "file_name": file.filename,
                "errors": [str(e)],
                "status": "error"
            })
    
    return {
        "uploaded": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }
```

### Example 7: Category Detection

```python
def auto_detect_category(filename: str) -> FileCategory:
    """Auto-detect file category from extension"""
    
    extension = Path(filename).suffix.lower()
    
    category_map = {
        ('.jpg', '.jpeg', '.png', '.gif', '.webp'): FileCategory.IMAGE,
        ('.pdf', '.doc', '.docx'): FileCategory.DOCUMENT,
        ('.xls', '.xlsx', '.csv'): FileCategory.SPREADSHEET,
        ('.mp4', '.avi', '.mov'): FileCategory.VIDEO,
        ('.mp3', '.wav', '.ogg'): FileCategory.AUDIO,
        ('.zip', '.tar', '.gz'): FileCategory.ARCHIVE,
    }
    
    for extensions, category in category_map.items():
        if extension in extensions:
            return category
    
    return FileCategory.ANY

# Usage
@router.post("/upload/auto")
async def upload_auto_detect(file: UploadFile = File(...)):
    """Auto-detect file category and validate"""
    
    category = auto_detect_category(file.filename)
    
    result = file_validator.validate_fastapi_upload(
        file=file,
        category=category
    )
    
    if not result.is_valid:
        raise HTTPException(status_code=400, detail=result.errors)
    
    return {"success": True, "category": category.value}
```

## Integration Examples

### 1. Restaurant Profile Image Upload

```python
# services/restaurant_service.py

from src.common.file_validator import file_validator, FileCategory

class RestaurantService:
    async def update_profile_image(
        self,
        restaurant_id: UUID,
        image_file: UploadFile,
    ) -> Dict[str, Any]:
        """Update restaurant profile image"""
        
        # Validate image
        result = file_validator.validate_fastapi_upload(
            file=image_file,
            category=FileCategory.IMAGE,
            save_to=Path(f"uploads/restaurants/{restaurant_id}/profile.jpg")
        )
        
        if not result.is_valid:
            raise InvalidFileTypeError(
                "Invalid image file",
                result.errors
            )
        
        # Update database with new image path
        restaurant = await self.repository.update(
            restaurant_id,
            {"profile_image": result.file_path}
        )
        
        # Upload to S3 (optional)
        # await upload_to_s3(result.file_path)
        
        return {
            "image_url": f"/media/{result.file_path}",
            "image_size": result.file_size,
            "dimensions": result.metadata
        }
```

### 2. Menu Item Image Upload

```python
# services/menu_service.py

class MenuService:
    async def add_menu_item_image(
        self,
        item_id: UUID,
        image_file: UploadFile,
    ):
        """Add image to menu item"""
        
        # Validate with specific dimensions
        result = file_validator.validate_fastapi_upload(
            file=image_file,
            category=FileCategory.IMAGE
        )
        
        # Additional validation through direct file check
        temp_path = Path(f"/tmp/{image_file.filename}")
        
        # Save temporarily
        with open(temp_path, "wb") as f:
            f.write(await image_file.read())
        
        # Validate dimensions
        result = file_validator.validate_file(
            file_path=temp_path,
            category=FileCategory.IMAGE,
            check_dimensions=True,
            max_width=1024,
            max_height=1024
        )
        
        if not result.is_valid:
            temp_path.unlink()  # Clean up
            raise InvalidFileTypeError("Invalid image", result.errors)
        
        # Move to final location
        final_path = Path(f"uploads/menu-items/{item_id}.jpg")
        temp_path.rename(final_path)
        
        return {"image_path": str(final_path)}
```

### 3. Document Upload with Verification

```python
# services/document_service.py

class DocumentService:
    async def upload_license(
        self,
        restaurant_id: UUID,
        license_file: UploadFile,
    ):
        """Upload restaurant license document"""
        
        # Validate document
        result = file_validator.validate_fastapi_upload(
            file=license_file,
            category=FileCategory.DOCUMENT,
            save_to=Path(f"uploads/documents/licenses/{restaurant_id}.pdf")
        )
        
        if not result.is_valid:
            raise InvalidFileTypeError("Invalid license document", result.errors)
        
        # Calculate hash for deduplication
        file_hash = result.metadata.get('sha256')
        
        # Check for duplicate
        existing = await self.repository.find_by_hash(file_hash)
        if existing:
            logger.warning("Duplicate document detected", hash=file_hash)
        
        # Store in database
        document = await self.repository.create({
            "restaurant_id": restaurant_id,
            "type": "license",
            "file_path": result.file_path,
            "file_name": result.file_name,
            "file_size": result.file_size,
            "mime_type": result.detected_mime_type,
            "hash": file_hash,
        })
        
        return document
```

## Error Handling

### Custom Exception Handling

```python
from fastapi import HTTPException, status

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        result = file_validator.validate_fastapi_upload(
            file=file,
            category=FileCategory.IMAGE
        )
        
        if not result.is_valid:
            # Return structured error response
            return {
                "success": False,
                "message": "File validation failed",
                "errors": result.errors,
                "warnings": result.warnings
            }
        
        return {"success": True, "file_info": result.to_dict()}
    
    except FileTooLargeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e)
        )
    
    except InvalidFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("File upload failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )
```

## Security Best Practices

### 1. Dangerous File Detection

The validator automatically blocks dangerous extensions:

```python
DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.com', '.scr',
    '.vbs', '.js', '.ps1', '.sh', '.jar', ...
}
```

### 2. Content Verification

Validates actual file content matches extension:

```python
# Detects if a .jpg file is actually a .exe
result = file_validator.validate_file(
    "malicious.jpg",  # Actually an executable renamed
    FileCategory.IMAGE
)
# Result will show MIME type mismatch warning
```

### 3. Script Injection Detection

Checks for dangerous content in text files:

```python
# Detects <script> tags in SVG files
# Detects javascript: in HTML
# Detects onerror= and similar XSS vectors
```

### 4. Safe File Naming

```python
import re
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove path traversal attempts
    filename = Path(filename).name
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}"

# Usage in upload
sanitized_name = sanitize_filename(file.filename)
result = file_validator.validate_upload(
    file_content=content,
    filename=sanitized_name,
    category=FileCategory.IMAGE
)
```

## Advanced Usage

### Custom Validation Rules

```python
from src.common.file_validator import FileValidator, FileCategory

class CustomFileValidator(FileValidator):
    """Extended validator with custom rules"""
    
    def validate_menu_csv(self, file_path: Path) -> FileValidationResult:
        """Validate menu CSV with custom rules"""
        
        # First, standard validation
        result = self.validate_file(file_path, FileCategory.SPREADSHEET)
        
        if not result.is_valid:
            return result
        
        # Custom validation: check CSV structure
        try:
            import csv
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                required_headers = {'name', 'price', 'category'}
                missing = required_headers - set(headers)
                
                if missing:
                    result.errors.append(
                        f"Missing required columns: {', '.join(missing)}"
                    )
                    result.is_valid = False
        
        except Exception as e:
            result.errors.append(f"CSV parsing failed: {str(e)}")
            result.is_valid = False
        
        return result
```

### Batch Validation

```python
def validate_directory(
    directory: Path,
    category: FileCategory
) -> Dict[str, FileValidationResult]:
    """Validate all files in directory"""
    
    results = {}
    
    for file_path in directory.glob('*'):
        if file_path.is_file():
            result = file_validator.validate_file(file_path, category)
            results[file_path.name] = result
    
    return results

# Usage
results = validate_directory(
    Path("uploads/pending"),
    FileCategory.IMAGE
)

# Print summary
valid = sum(1 for r in results.values() if r.is_valid)
print(f"Valid: {valid}/{len(results)}")
```

## Testing

### Unit Tests

```python
# tests/test_file_validator.py

import pytest
from pathlib import Path
from src.common.file_validator import file_validator, FileCategory

def test_valid_image():
    """Test valid image validation"""
    result = file_validator.validate_file(
        "tests/fixtures/valid_image.jpg",
        FileCategory.IMAGE
    )
    assert result.is_valid
    assert result.detected_mime_type == "image/jpeg"

def test_invalid_extension():
    """Test invalid extension rejection"""
    result = file_validator.validate_file(
        "tests/fixtures/document.exe",
        FileCategory.IMAGE
    )
    assert not result.is_valid
    assert any("extension" in err.lower() for err in result.errors)

def test_file_too_large():
    """Test file size limit"""
    # Create large file
    large_file = Path("tests/fixtures/large.jpg")
    large_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11 MB
    
    result = file_validator.validate_file(
        large_file,
        FileCategory.IMAGE
    )
    assert not result.is_valid
    assert any("size" in err.lower() for err in result.errors)

def test_mime_type_mismatch():
    """Test MIME type mismatch detection"""
    # Create fake image (text file with .jpg extension)
    fake_image = Path("tests/fixtures/fake.jpg")
    fake_image.write_text("This is not an image")
    
    result = file_validator.validate_file(
        fake_image,
        FileCategory.IMAGE
    )
    assert not result.is_valid or result.warnings
```

## Monitoring & Logging

All validation operations are logged with structured logging:

```python
# Successful validation
logger.info(
    "File validation completed",
    file_name="menu.jpg",
    category="image",
    is_valid=True,
    errors=0,
    warnings=0
)

# Failed validation
logger.warning(
    "File validation completed",
    file_name="document.exe",
    category="document",
    is_valid=False,
    errors=2,
    warnings=1
)
```

## Production Checklist

- [ ] Configure max upload sizes in settings
- [ ] Define allowed extensions per category
- [ ] Set up upload directory structure
- [ ] Configure file storage (local/S3)
- [ ] Implement virus scanning (ClamAV)
- [ ] Set up monitoring for upload failures
- [ ] Configure rate limiting for uploads
- [ ] Implement file cleanup for old uploads
- [ ] Set up backup strategy for uploads
- [ ] Configure CDN for serving uploads
- [ ] Implement image optimization pipeline
- [ ] Set up access control for uploads
- [ ] Configure CORS for upload endpoints
- [ ] Test with various file types
- [ ] Document upload limits for users

## Dependencies

Required packages (add to requirements.txt):

```txt
# Already included in your requirements
python-multipart==0.0.20  # For file uploads in FastAPI

# Optional for enhanced image validation
Pillow==10.1.0  # For image dimension checks
```

## Common Issues & Solutions

### Issue: "MIME type could not be determined"

**Solution**: Install Pillow for better image detection:
```bash
pip install Pillow
```

### Issue: Large file uploads timing out

**Solution**: Increase timeout and add streaming:
```python
@router.post("/upload")
async def upload_large_file(
    file: UploadFile = File(...),
    chunk_size: int = 1024 * 1024  # 1 MB chunks
):
    # Stream large files
    ...
```

### Issue: High memory usage with many uploads

**Solution**: Process files in chunks and clean up:
```python
# Don't read entire file into memory
# Use streaming validation
```

This file validation utility provides enterprise-grade validation with security, performance, and maintainability built-in!