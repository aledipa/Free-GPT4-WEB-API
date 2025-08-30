"""Validation utilities for FreeGPT4 Web API."""

import re
from typing import Optional, Dict, Any
from werkzeug.datastructures import FileStorage

def validate_proxy_format(proxy: str) -> bool:
    """Validate proxy format.
    
    Args:
        proxy: Proxy string in format protocol://user:password@host:port
        
    Returns:
        True if valid, False otherwise
    """
    proxy_pattern = re.compile(
        r'^(https?|socks[45])://[^:]+:[^@]+@[^:]+:\d+$'
    )
    return bool(proxy_pattern.match(proxy))

def validate_token_format(token: str) -> bool:
    """Validate token format (UUID4).
    
    Args:
        token: Token string
        
    Returns:
        True if valid UUID4, False otherwise
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(token))

def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """Validate username.
    
    Args:
        username: Username string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be less than 50 characters long"
    
    if username.lower() == "admin":
        return False, "Username 'admin' is reserved"
    
    # Allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None

def validate_password(password: str, min_length: int = 8) -> tuple[bool, Optional[str]]:
    """Validate password strength.
    
    Args:
        password: Password string
        min_length: Minimum password length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    return True, None

def validate_file_upload(file: FileStorage, allowed_extensions: set) -> tuple[bool, Optional[str]]:
    """Validate file upload.
    
    Args:
        file: Uploaded file
        allowed_extensions: Set of allowed file extensions
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file provided"
    
    if '.' not in file.filename:
        return False, "File must have an extension"
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension not in allowed_extensions:
        return False, f"File extension '{extension}' not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    return True, None

def validate_port(port: str) -> tuple[bool, Optional[str]]:
    """Validate port number.
    
    Args:
        port: Port string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            return False, "Port must be between 1 and 65535"
        return True, None
    except ValueError:
        return False, "Port must be a valid number"

def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Sanitize input string.
    
    Args:
        value: Input string
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove null bytes and other control characters
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str(value))
    
    # Trim to max length
    return sanitized[:max_length].strip()

def validate_provider(provider: str, available_providers: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate AI provider.
    
    Args:
        provider: Provider name
        available_providers: Dict of available providers
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not provider:
        return False, "Provider cannot be empty"
    
    if provider not in available_providers:
        return False, f"Provider '{provider}' not available. Available: {', '.join(available_providers.keys())}"
    
    return True, None

def validate_model(model: str) -> tuple[bool, Optional[str]]:
    """Validate AI model.
    
    Args:
        model: Model name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not model:
        return False, "Model cannot be empty"
    
    if len(model) > 100:
        return False, "Model name too long"
    
    return True, None
