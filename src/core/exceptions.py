# src/core/exceptions.py

"""
Custom exception classes for the application
Provides structured error handling with error codes
"""


class AppException(Exception):
    """
    Base exception for all application errors
    All custom exceptions should inherit from this class
    """
    
    def __init__(self, message: str, error_code: str = "APP_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r}, error_code={self.error_code!r})"


# ============================================================================
# Authentication & Authorization Exceptions
# ============================================================================

class AuthenticationError(AppException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid"""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)
        self.error_code = "INVALID_CREDENTIALS"


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired"""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)
        self.error_code = "TOKEN_EXPIRED"


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid"""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)
        self.error_code = "INVALID_TOKEN"


class AuthorizationError(AppException):
    """Raised when user doesn't have permission"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions"""
    
    def __init__(self, message: str = "You don't have permission to perform this action"):
        super().__init__(message)
        self.error_code = "INSUFFICIENT_PERMISSIONS"


# ============================================================================
# Resource Exceptions
# ============================================================================

class NotFoundError(AppException):
    """Raised when a resource is not found"""
    
    def __init__(self, resource: str = "Resource", resource_id: str = None):
        if resource_id:
            message = f"{resource} with ID '{resource_id}' not found"
        else:
            message = f"{resource} not found"
        super().__init__(message, "NOT_FOUND")


class AlreadyExistsError(AppException):
    """Raised when trying to create a resource that already exists"""
    
    def __init__(self, resource: str = "Resource", identifier: str = None):
        if identifier:
            message = f"{resource} with identifier '{identifier}' already exists"
        else:
            message = f"{resource} already exists"
        super().__init__(message, "ALREADY_EXISTS")


class ConflictError(AppException):
    """Raised when there's a conflict with current state"""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, "CONFLICT")


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationError(AppException):
    """Raised when data validation fails"""
    
    def __init__(self, message: str = "Validation failed", field: str = None):
        if field:
            message = f"Validation failed for field '{field}': {message}"
        super().__init__(message, "VALIDATION_ERROR")


class InvalidInputError(ValidationError):
    """Raised when input data is invalid"""
    
    def __init__(self, message: str = "Invalid input", field: str = None):
        super().__init__(message, field)
        self.error_code = "INVALID_INPUT"


class MissingFieldError(ValidationError):
    """Raised when a required field is missing"""
    
    def __init__(self, field: str):
        super().__init__(f"Required field '{field}' is missing")
        self.error_code = "MISSING_FIELD"


# ============================================================================
# Business Logic Exceptions
# ============================================================================

class BusinessLogicError(AppException):
    """Raised when business logic validation fails"""
    
    def __init__(self, message: str = "Business logic error"):
        super().__init__(message, "BUSINESS_LOGIC_ERROR")


class InsufficientBalanceError(BusinessLogicError):
    """Raised when account has insufficient balance"""
    
    def __init__(self, message: str = "Insufficient balance"):
        super().__init__(message)
        self.error_code = "INSUFFICIENT_BALANCE"


class OrderNotAllowedError(BusinessLogicError):
    """Raised when order operation is not allowed"""
    
    def __init__(self, message: str = "Order operation not allowed"):
        super().__init__(message)
        self.error_code = "ORDER_NOT_ALLOWED"


class DeliveryNotAvailableError(BusinessLogicError):
    """Raised when delivery is not available"""
    
    def __init__(self, message: str = "Delivery not available in this area"):
        super().__init__(message)
        self.error_code = "DELIVERY_NOT_AVAILABLE"


class RestaurantClosedError(BusinessLogicError):
    """Raised when restaurant is closed"""
    
    def __init__(self, message: str = "Restaurant is currently closed"):
        super().__init__(message)
        self.error_code = "RESTAURANT_CLOSED"


class ItemOutOfStockError(BusinessLogicError):
    """Raised when menu item is out of stock"""
    
    def __init__(self, item_name: str = "Item"):
        super().__init__(f"{item_name} is currently out of stock")
        self.error_code = "ITEM_OUT_OF_STOCK"


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseError(AppException):
    """Raised when database operation fails"""
    
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, "DATABASE_ERROR")


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(message)
        self.error_code = "DB_CONNECTION_ERROR"


class TransactionError(DatabaseError):
    """Raised when transaction fails"""
    
    def __init__(self, message: str = "Transaction failed"):
        super().__init__(message)
        self.error_code = "TRANSACTION_ERROR"


# ============================================================================
# External Service Exceptions
# ============================================================================

class ExternalServiceError(AppException):
    """Raised when external service call fails"""
    
    def __init__(self, service: str = "External service", message: str = None):
        if message:
            full_message = f"{service} error: {message}"
        else:
            full_message = f"{service} is unavailable"
        super().__init__(full_message, "EXTERNAL_SERVICE_ERROR")


class PaymentGatewayError(ExternalServiceError):
    """Raised when payment gateway fails"""
    
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__("Payment gateway", message)
        self.error_code = "PAYMENT_GATEWAY_ERROR"


class DeliveryProviderError(ExternalServiceError):
    """Raised when delivery provider API fails"""
    
    def __init__(self, provider: str = "Delivery provider", message: str = None):
        super().__init__(provider, message)
        self.error_code = "DELIVERY_PROVIDER_ERROR"


class SMSServiceError(ExternalServiceError):
    """Raised when SMS service fails"""
    
    def __init__(self, message: str = "Failed to send SMS"):
        super().__init__("SMS service", message)
        self.error_code = "SMS_SERVICE_ERROR"


class EmailServiceError(ExternalServiceError):
    """Raised when email service fails"""
    
    def __init__(self, message: str = "Failed to send email"):
        super().__init__("Email service", message)
        self.error_code = "EMAIL_SERVICE_ERROR"


# ============================================================================
# Rate Limiting Exceptions
# ============================================================================

class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")


# ============================================================================
# File Upload Exceptions
# ============================================================================

class FileUploadError(AppException):
    """Raised when file upload fails"""
    
    def __init__(self, message: str = "File upload failed"):
        super().__init__(message, "FILE_UPLOAD_ERROR")


class FileTooLargeError(FileUploadError):
    """Raised when uploaded file is too large"""
    
    def __init__(self, max_size: int):
        super().__init__(f"File size exceeds maximum allowed size of {max_size} bytes")
        self.error_code = "FILE_TOO_LARGE"


class InvalidFileTypeError(FileUploadError):
    """Raised when file type is not allowed"""
    
    def __init__(self, file_type: str, allowed_types: list[str]):
        super().__init__(
            f"File type '{file_type}' is not allowed. Allowed types: {', '.join(allowed_types)}"
        )
        self.error_code = "INVALID_FILE_TYPE"


# ============================================================================
# User-specific Exceptions
# ============================================================================

class UserAlreadyExistsError(AlreadyExistsError):
    """Raised when user already exists"""
    
    def __init__(self, identifier: str):
        super().__init__("User", identifier)


class UserNotFoundError(NotFoundError):
    """Raised when user is not found"""
    
    def __init__(self, user_id: str = None):
        super().__init__("User", user_id)


class UserInactiveError(BusinessLogicError):
    """Raised when user account is inactive"""
    
    def __init__(self, message: str = "User account is inactive"):
        super().__init__(message)
        self.error_code = "USER_INACTIVE"


class UserBlockedError(BusinessLogicError):
    """Raised when user account is blocked"""
    
    def __init__(self, message: str = "User account has been blocked"):
        super().__init__(message)
        self.error_code = "USER_BLOCKED"


# ============================================================================
# Order-specific Exceptions
# ============================================================================

class OrderNotFoundError(NotFoundError):
    """Raised when order is not found"""
    
    def __init__(self, order_id: str = None):
        super().__init__("Order", order_id)


class InvalidOrderStatusError(BusinessLogicError):
    """Raised when order status transition is invalid"""
    
    def __init__(self, current_status: str, new_status: str):
        super().__init__(
            f"Cannot change order status from '{current_status}' to '{new_status}'"
        )
        self.error_code = "INVALID_ORDER_STATUS"


# ============================================================================
# Restaurant-specific Exceptions
# ============================================================================

class RestaurantNotFoundError(NotFoundError):
    """Raised when restaurant is not found"""
    
    def __init__(self, restaurant_id: str = None):
        super().__init__("Restaurant", restaurant_id)


class RestaurantNotActiveError(BusinessLogicError):
    """Raised when restaurant is not active"""
    
    def __init__(self, message: str = "Restaurant is not currently active"):
        super().__init__(message)
        self.error_code = "RESTAURANT_NOT_ACTIVE"