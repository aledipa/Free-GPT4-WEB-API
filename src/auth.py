"""Authentication and authorization utilities."""

from typing import Optional, Dict, Any
from functools import wraps
from flask import request, session

from database import db_manager
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.logging import logger
from utils.validation import validate_token_format

class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self):
        self.db = db_manager
    
    def authenticate_admin(self, username: str, password: str) -> bool:
        """Authenticate admin user.
        
        Args:
            username: Username (must be 'admin')
            password: Password
            
        Returns:
            True if authentication successful
        """
        if username != "admin":
            return False
        
        return self.db.verify_admin_password(password)
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate regular user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if authentication successful
        """
        return self.db.verify_user_password(username, password)
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user by token.
        
        Args:
            token: User token
            
        Returns:
            User data or None if not found/invalid
        """
        if not validate_token_format(token):
            return None
        
        # Check if it's admin token
        settings = self.db.get_settings()
        if settings.get("token") == token:
            return {
                "username": "admin",
                "token": token,
                "is_admin": True
            }
        
        # Check regular users
        user = self.db.get_user_by_token(token)
        if user:
            user["is_admin"] = False
        
        return user
    
    def verify_token_access(self, token: str, private_mode: bool = False) -> Optional[str]:
        """Verify token access and return username.
        
        Args:
            token: Access token
            private_mode: Whether private mode is enabled
            
        Returns:
            Username if authorized, None otherwise
        """
        if private_mode and not token:
            return None
        
        if not token:
            return "admin" if not private_mode else None
        
        user = self.get_user_by_token(token)
        return user["username"] if user else None

def require_auth(admin_only: bool = False):
    """Decorator to require authentication.
    
    Args:
        admin_only: Whether to require admin privileges
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_service = AuthService()
            
            if request.method == "POST":
                username = request.form.get("username")
                password = request.form.get("password")
                
                if not username or not password:
                    raise AuthenticationError("Username and password required")
                
                if admin_only or username == "admin":
                    if not auth_service.authenticate_admin(username, password):
                        raise AuthenticationError("Invalid admin credentials")
                else:
                    if not auth_service.authenticate_user(username, password):
                        raise AuthenticationError("Invalid user credentials")
                
                # Store authenticated user in session/context
                session["authenticated_user"] = username
                session["is_admin"] = (username == "admin")
            else:
                # For GET requests, check if already authenticated
                if not session.get("authenticated_user"):
                    raise AuthenticationError("Authentication required")
                
                if admin_only and not session.get("is_admin"):
                    raise AuthorizationError("Admin access required")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_token_auth(private_mode: bool = False, virtual_users: bool = False):
    """Decorator to require token-based authentication.
    
    Args:
        private_mode: Whether private mode is enabled
        virtual_users: Whether virtual users are enabled
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_service = AuthService()
            
            token = request.args.get("token")
            username = auth_service.verify_token_access(token, private_mode)
            
            if private_mode and not username:
                raise AuthenticationError("Invalid or missing token")
            
            if virtual_users and not username:
                raise AuthenticationError("Token required for virtual users")
            
            # Add user context to request
            request.current_user = username or "admin"
            request.is_admin = (username == "admin") if username else True
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Global auth service instance
auth_service = AuthService()
