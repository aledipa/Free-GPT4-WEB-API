"""Exception classes for FreeGPT4 Web API."""

class FreeGPTException(Exception):
    """Base exception for FreeGPT4 Web API."""
    pass

class DatabaseError(FreeGPTException):
    """Database operation error."""
    pass

class ValidationError(FreeGPTException):
    """Validation error."""
    pass

class AuthenticationError(FreeGPTException):
    """Authentication error."""
    pass

class AuthorizationError(FreeGPTException):
    """Authorization error."""
    pass

class ConfigurationError(FreeGPTException):
    """Configuration error."""
    pass

class AIProviderError(FreeGPTException):
    """AI provider error."""
    pass

class FileUploadError(FreeGPTException):
    """File upload error."""
    pass
