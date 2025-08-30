"""Utility functions for FreeGPT4 Web API."""

import json
import random
import re
from typing import Optional, Dict, Any, List
from uuid import uuid4
from pathlib import Path

from .logging import logger

def generate_uuid() -> str:
    """Generate a new UUID4 string.
    
    Returns:
        UUID4 string
    """
    return str(uuid4())

def load_json_file(file_path: Path, default: Any = None) -> Any:
    """Load JSON data from file.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Loaded JSON data or default value
    """
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load JSON file {file_path}: {e}")
    
    return default

def save_json_file(file_path: Path, data: Any) -> bool:
    """Save data to JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False

def clean_response_sources(response: str) -> str:
    """Remove source references from AI response.
    
    Args:
        response: AI response text
        
    Returns:
        Cleaned response text
    """
    if not response:
        return response
    
    # Remove source references like [^1^][1]
    if re.search(r"\[\^[0-9]+\^\]\[[0-9]+\]", response):
        response_parts = response.split("\n\n")
        if len(response_parts) > 1:
            response_parts.pop(0)  # Remove first part (usually sources)
        response = re.sub(r"\[\^[0-9]+\^\]\[[0-9]+\]", "", str(response_parts[0]) if response_parts else "")
    
    return response.strip()

def format_proxy_url(proxy_dict: Dict[str, str]) -> str:
    """Format proxy dictionary to URL string.
    
    Args:
        proxy_dict: Dictionary with proxy configuration
        
    Returns:
        Formatted proxy URL
    """
    return f"{proxy_dict['protocol']}://{proxy_dict['username']}:{proxy_dict['password']}@{proxy_dict['ip']}:{proxy_dict['port']}"

def parse_proxy_url(proxy_url: str) -> Optional[Dict[str, str]]:
    """Parse proxy URL to dictionary.
    
    Args:
        proxy_url: Proxy URL string
        
    Returns:
        Dictionary with proxy configuration or None if invalid
    """
    if not proxy_url or proxy_url.count(":") != 3 or proxy_url.count("@") != 1:
        return None
    
    try:
        parts = proxy_url.split("://")
        protocol = parts[0]
        
        rest = parts[1]
        auth_and_host = rest.split("@")
        auth = auth_and_host[0]
        host_and_port = auth_and_host[1]
        
        username, password = auth.split(":", 1)
        ip, port = host_and_port.split(":")
        
        return {
            "protocol": protocol,
            "username": username,
            "password": password,
            "ip": ip,
            "port": port
        }
    except (IndexError, ValueError):
        return None

def select_random_proxy(proxies: List[Dict[str, str]]) -> Optional[str]:
    """Select a random proxy from the list.
    
    Args:
        proxies: List of proxy dictionaries
        
    Returns:
        Formatted proxy URL or None if no proxies
    """
    if not proxies:
        return None
    
    proxy_dict = random.choice(proxies)
    return format_proxy_url(proxy_dict)

def create_dummy_cookies() -> Dict[str, str]:
    """Create dummy cookies for requests.
    
    Returns:
        Dictionary with dummy cookies
    """
    return {"dummy": "value"}

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove path separators and other dangerous characters
    safe_name = re.sub(r'[^\w\s\-_\.]', '', filename)
    # Replace multiple spaces/underscores with single underscore
    safe_name = re.sub(r'[\s_]+', '_', safe_name)
    return safe_name.strip('_.')[:255]  # Limit length

def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data for logging.
    
    Args:
        data: Sensitive data string
        mask_char: Character to use for masking
        visible_chars: Number of characters to show at the end
        
    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]
