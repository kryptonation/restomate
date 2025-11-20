# Food fleet Modular Application - Complete API Documentation

## Table of Contents
1. [Authentication APIs](#authentication-apis)
2. [User Management APIs](#user-management-apis)
3. [Role & Permission APIs](#role--permission-apis)
4. [Error Responses](#error-responses)
5. [Request/Response Examples](#requestresponse-examples)
6. [SDK & Client Examples](#sdk--client-examples)

---

## Base URL

```
Development: http://localhost:8000
Production: https://api.yourdomain.com
```

All API endpoints are prefixed with `/api/v1` unless otherwise specified.

---

## Authentication APIs

### Register User

Create a new user account.

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "role_id": 2
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "status": "active",
  "two_fa_enabled": false,
  "role": {
    "id": 2,
    "name": "user",
    "description": "Regular user",
    "is_active": true,
    "is_system": false,
    "permissions": [],
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  },
  "last_login_at": null,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

**Validation Rules:**
- Email must be valid and unique
- Username: 3-100 characters, unique
- Password: minimum 8 characters, must contain uppercase, lowercase, digit, and special character
- Phone number: optional, E.164 format recommended

---

### Login

Authenticate user and receive JWT tokens.

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "totp_code": "123456"
}
```

**Fields:**
- `email` (required): User's email address
- `password` (required): User's password
- `totp_code` (optional): 6-digit 2FA code (required if 2FA enabled)

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_verified": true,
    "two_fa_enabled": false,
    "role": {...},
    "last_login_at": "2025-01-15T10:30:00Z",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `401 Unauthorized`: Account locked (after 5 failed attempts)
- `401 Unauthorized`: 2FA code required
- `401 Unauthorized`: Invalid 2FA code

---

### Refresh Access Token

Obtain a new access token using refresh token.

**Endpoint:** `POST /api/v1/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Lifetime:**
- Access Token: 30 minutes
- Refresh Token: 7 days

---

### Logout

Logout from current session (revokes refresh token).

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

---

### Logout All Sessions

Logout from all devices/sessions.

**Endpoint:** `POST /api/v1/auth/logout-all`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Logged out from all sessions"
}
```

---

## Password Management APIs

### Change Password

Change password for authenticated user.

**Endpoint:** `POST /api/v1/auth/password/change`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Notes:**
- All existing sessions will be terminated
- User must login again with new password
- Cannot reuse current password

---

### Request Password Reset

Request password reset link via email.

**Endpoint:** `POST /api/v1/auth/password/reset-request`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

**Notes:**
- Always returns success to prevent email enumeration
- Reset token valid for 15 minutes
- Email contains reset link with token

---

### Reset Password

Reset password using token from email.

**Endpoint:** `POST /api/v1/auth/password/reset`

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

---

## Email Verification APIs

### Send Verification Email

Send or resend email verification link.

**Endpoint:** `POST /api/v1/auth/email/send-verification`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Verification email sent"
}
```

---

### Verify Email

Verify email address using token.

**Endpoint:** `POST /api/v1/auth/email/verify`

**Request Body:**
```json
{
  "token": "verification-token-from-email"
}
```

**Response:** `200 OK`
```json
{
  "message": "Email verified successfully"
}
```

---

## Two-Factor Authentication APIs

### Setup 2FA

Initiate 2FA setup - generates QR code and backup codes.

**Endpoint:** `POST /api/v1/auth/2fa/setup`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "backup_codes": [
    "A1B2C3D4",
    "E5F6G7H8",
    "I9J0K1L2",
    "M3N4O5P6",
    "Q7R8S9T0",
    "U1V2W3X4",
    "Y5Z6A7B8",
    "C9D0E1F2",
    "G3H4I5J6",
    "K7L8M9N0"
  ],
  "provisioning_uri": "otpauth://totp/FastAPI%20App:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=FastAPI%20App"
}
```

**Usage:**
1. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
2. Save backup codes securely
3. Enable 2FA with verification code

---

### Enable 2FA

Enable 2FA after verifying TOTP code.

**Endpoint:** `POST /api/v1/auth/2fa/enable`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "totp_code": "123456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Two-factor authentication enabled successfully",
  "backup_codes": [
    "A1B2C3D4",
    "E5F6G7H8",
    ...
  ]
}
```

---

### Disable 2FA

Disable two-factor authentication.

**Endpoint:** `POST /api/v1/auth/2fa/disable`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "password": "CurrentPass123!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Two-factor authentication disabled successfully"
}
```

---

### Regenerate Backup Codes

Generate new backup codes (invalidates old ones).

**Endpoint:** `POST /api/v1/auth/2fa/regenerate-backup-codes`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "password": "CurrentPass123!"
}
```

**Response:** `200 OK`
```json
{
  "backup_codes": [
    "X1Y2Z3A4",
    "B5C6D7E8",
    ...
  ]
}
```

---

## User Management APIs

### Get Current User Profile

Get authenticated user's profile.

**Endpoint:** `GET /api/v1/users/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "is_active": true,
  "is_verified": true,
  "is_superuser": false,
  "status": "active",
  "two_fa_enabled": true,
  "role": {
    "id": 2,
    "name": "user",
    "permissions": [...]
  },
  "last_login_at": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### Update Current User Profile

Update authenticated user's profile.

**Endpoint:** `PUT /api/v1/users/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_number": "+1987654321"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_number": "+1987654321",
  ...
}
```

---

### List All Users (Admin)

List all users with pagination.

**Endpoint:** `GET /api/v1/users`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100, max: 1000)
- `is_active` (optional): Filter by active status (true/false)

**Example:**
```
GET /api/v1/users?skip=0&limit=50&is_active=true
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "email": "user1@example.com",
    "username": "user1",
    ...
  },
  {
    "id": 2,
    "email": "user2@example.com",
    "username": "user2",
    ...
  }
]
```

---

### Get User by ID (Admin)

Get specific user by ID.

**Endpoint:** `GET /api/v1/users/{user_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  ...
}
```

---

### Delete User (Admin)

Delete user (soft delete).

**Endpoint:** `DELETE /api/v1/users/{user_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

---

## Role & Permission APIs

### Create Role

Create a new role with permissions.

**Endpoint:** `POST /api/v1/roles`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "editor",
  "description": "Content editor role",
  "is_active": true,
  "permission_ids": [1, 2, 3, 4]
}
```

**Response:** `201 Created`
```json
{
  "id": 3,
  "name": "editor",
  "description": "Content editor role",
  "is_active": true,
  "is_system": false,
  "permissions": [
    {
      "id": 1,
      "name": "articles:create",
      "resource": "articles",
      "action": "create",
      "description": "Create articles",
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    },
    ...
  ],
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

---

### List Roles

List all roles.

**Endpoint:** `GET /api/v1/roles`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100)
- `is_active` (optional): Filter by active status

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "admin",
    "description": "Administrator role",
    "is_active": true,
    "is_system": true,
    "permissions": [...]
  },
  {
    "id": 2,
    "name": "user",
    "description": "Regular user role",
    "is_active": true,
    "is_system": false,
    "permissions": [...]
  }
]
```

---

### Get Role by ID

Get specific role with permissions.

**Endpoint:** `GET /api/v1/roles/{role_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "admin",
  "description": "Administrator role",
  "is_active": true,
  "is_system": true,
  "permissions": [
    {
      "id": 1,
      "name": "users:create",
      "resource": "users",
      "action": "create",
      ...
    },
    ...
  ]
}
```

---

### Update Role

Update role information.

**Endpoint:** `PUT /api/v1/roles/{role_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "content_editor",
  "description": "Updated description",
  "is_active": true
}
```

**Response:** `200 OK`
```json
{
  "id": 3,
  "name": "content_editor",
  "description": "Updated description",
  ...
}
```

**Note:** System roles cannot be updated.

---

### Delete Role

Delete a role.

**Endpoint:** `DELETE /api/v1/roles/{role_id}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

**Note:** System roles cannot be deleted.

---

### Add Permissions to Role

Add permissions to an existing role.

**Endpoint:** `POST /api/v1/roles/{role_id}/permissions`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "permission_ids": [5, 6, 7]
}
```

**Response:** `200 OK`
```json
{
  "id": 3,
  "name": "editor",
  "permissions": [
    ...,
    {
      "id": 5,
      "name": "comments:create",
      ...
    }
  ]
}
```

---

### Remove Permissions from Role

Remove permissions from a role.

**Endpoint:** `DELETE /api/v1/roles/{role_id}/permissions`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "permission_ids": [5, 6]
}
```

**Response:** `200 OK`
```json
{
  "id": 3,
  "name": "editor",
  "permissions": [...]
}
```

---

## Error Responses

All error responses follow this structure:

```json
{
  "error": "Error message",
  "details": {
    "field": "additional_info"
  }
}
```

### Common HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Examples

**401 Unauthorized:**
```json
{
  "error": "Invalid email or password",
  "details": {}
}
```

**403 Forbidden:**
```json
{
  "error": "Insufficient permissions to delete products",
  "details": {
    "resource": "products",
    "action": "delete"
  }
}
```

**404 Not Found:**
```json
{
  "error": "User with ID 999 not found",
  "details": {
    "user_id": 999
  }
}
```

**422 Validation Error:**
```json
{
  "error": "Validation error",
  "details": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 8}
    }
  ]
}
```

---

## Request/Response Examples

### Complete Registration Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "SecurePass123!",
    "first_name": "New",
    "last_name": "User"
  }'

# 2. Verify Email (check email for token)
curl -X POST http://localhost:8000/api/v1/auth/email/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "verification-token-from-email"
  }'

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!"
  }'
```

### Complete 2FA Setup Flow

```bash
# 1. Login and get access token
ACCESS_TOKEN="your-access-token"

# 2. Setup 2FA
curl -X POST http://localhost:8000/api/v1/auth/2fa/setup \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Response includes QR code and backup codes
# Scan QR code with authenticator app

# 3. Enable 2FA with code from app
curl -X POST http://localhost:8000/api/v1/auth/2fa/enable \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "totp_code": "123456"
  }'

# 4. Next login requires 2FA code
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "totp_code": "654321"
  }'
```

---

## SDK & Client Examples

### Python SDK

```python
import httpx
from typing import Optional

class FastAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def register(self, email: str, username: str, password: str, **kwargs):
        """Register a new user."""
        response = await self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def login(self, email: str, password: str, totp_code: Optional[str] = None):
        """Login and store tokens."""
        data = {"email": email, "password": password}
        if totp_code:
            data["totp_code"] = totp_code
        
        response = await self.client.post("/api/v1/auth/login", json=data)
        response.raise_for_status()
        
        result = response.json()
        self.access_token = result["access_token"]
        self.refresh_token = result["refresh_token"]
        return result
    
    async def get_profile(self):
        """Get current user profile."""
        response = await self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        return response.json()
    
    async def refresh_access_token(self):
        """Refresh access token."""
        response = await self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        result = response.json()
        self.access_token = result["access_token"]
        return result
    
    async def close(self):
        """Close client connection."""
        await self.client.aclose()

# Usage
async def main():
    client = FastAPIClient("http://localhost:8000")
    
    # Register
    user = await client.register(
        email="test@example.com",
        username="testuser",
        password="SecurePass123!"
    )
    print(f"Registered user: {user['id']}")
    
    # Login
    await client.login("test@example.com", "SecurePass123!")
    print("Logged in successfully")
    
    # Get profile
    profile = await client.get_profile()
    print(f"Profile: {profile['email']}")
    
    await client.close()
```

### JavaScript/TypeScript SDK

```typescript
// fastapi-client.ts
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_verified: boolean;
  two_fa_enabled: boolean;
}

class FastAPIClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async register(data: {
    email: string;
    username: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }): Promise<User> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(await response.text());
    }
    
    return response.json();
  }

  async login(
    email: string,
    password: string,
    totpCode?: string
  ): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ email, password, totp_code: totpCode })
    });
    
    if (!response.ok) {
      throw new Error(await response.text());
    }
    
    const data: LoginResponse = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    
    // Store in localStorage
    localStorage.setItem('access_token', this.accessToken);
    localStorage.setItem('refresh_token', this.refreshToken);
    
    return data;
  }

  async getProfile(): Promise<User> {
    return this.authenticatedRequest('/api/v1/users/me');
  }

  async updateProfile(data: {
    first_name?: string;
    last_name?: string;
    phone_number?: string;
  }): Promise<User> {
    return this.authenticatedRequest('/api/v1/users/me', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  private async authenticatedRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<any> {
    let response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.accessToken}`,
        ...options.headers
      }
    });

    // If unauthorized, try refreshing token
    if (response.status === 401) {
      await this.refreshAccessToken();
      
      response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.accessToken}`,
          ...options.headers
        }
      });
    }

    if (!response.ok) {
      throw new Error(await response.text());
    }

    return response.json();
  }

  private async refreshAccessToken(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ refresh_token: this.refreshToken })
    });

    if (!response.ok) {
      // Refresh token expired, logout
      this.logout();
      throw new Error('Session expired');
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    localStorage.setItem('access_token', this.accessToken);
  }

  logout(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

// Usage
const client = new FastAPIClient('http://localhost:8000');

// Register
await client.register({
  email: 'test@example.com',
  username: 'testuser',
  password: 'SecurePass123!'
});

// Login
await client.login('test@example.com', 'SecurePass123!');

// Get profile
const profile = await client.getProfile();
console.log(profile);
```

This comprehensive API documentation provides all the information needed to integrate with the FastAPI application!