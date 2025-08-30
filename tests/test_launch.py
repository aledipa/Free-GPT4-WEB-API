"""Test suite for FreeGPT4 Web API refactored modules."""

import pytest
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBasicFunctionality:
    """Test basic functionality without problematic dependencies."""
    
    def test_basic_assertion(self):
        """Basic test to verify pytest is working."""
        assert True
    
    def test_python_version(self):
        """Verify Python version is acceptable."""
        assert sys.version_info >= (3, 9)


class TestConfigModule:
    """Test configuration module functionality."""
    
    def test_config_import(self):
        """Test if config module imports correctly."""
        from config import Config
        assert Config is not None
    
    def test_config_properties(self):
        """Test configuration properties."""
        from config import Config
        config = Config()
        assert hasattr(config, 'database')
        assert hasattr(config, 'server')
        assert hasattr(config, 'security')


class TestDatabaseModule:
    """Test database module functionality."""
    
    def test_database_import(self):
        """Test if database module imports correctly."""
        from database import DatabaseManager
        assert DatabaseManager is not None
    
    def test_database_manager_creation(self):
        """Test database manager creation."""
        from database import DatabaseManager
        db_manager = DatabaseManager(':memory:')
        assert db_manager is not None
        assert hasattr(db_manager, 'get_connection')


class TestAuthModule:
    """Test authentication module functionality."""
    
    def test_auth_import(self):
        """Test if auth module imports correctly."""
        from auth import AuthService
        assert AuthService is not None
    
    def test_auth_service_creation(self):
        """Test auth service creation."""
        from auth import AuthService
        auth_service = AuthService()
        assert auth_service is not None
        assert hasattr(auth_service, 'authenticate_admin')


class TestValidationModule:
    """Test validation module functionality."""
    
    def test_validation_import(self):
        """Test if validation module imports correctly."""
        from utils.validation import validate_proxy_format, validate_token_format
        assert callable(validate_proxy_format)
        assert callable(validate_token_format)
    
    def test_proxy_validation(self):
        """Test proxy format validation."""
        from utils.validation import validate_proxy_format
        
        # Valid proxy formats
        assert validate_proxy_format("http://user:pass@127.0.0.1:8080")
        assert validate_proxy_format("https://user:pass@proxy.example.com:3128")
        
        # Invalid proxy formats
        assert not validate_proxy_format("not_a_proxy")
        assert not validate_proxy_format("ftp://invalid.com")
        assert not validate_proxy_format("")
        assert not validate_proxy_format("http://127.0.0.1:8080")  # missing auth
    
    def test_token_validation(self):
        """Test token validation."""
        from utils.validation import validate_token_format
        
        # Valid UUID4 tokens  
        assert validate_token_format("12345678-1234-4567-8901-123456789012")
        assert validate_token_format("a1b2c3d4-e5f6-4789-a012-b3c4d5e6f789")
        
        # Invalid tokens
        assert not validate_token_format("invalid_token")
        assert not validate_token_format("12345678-1234-1234-1234-123456789012")  # not UUID4
        assert not validate_token_format("")


class TestExceptionsModule:
    """Test custom exceptions module."""
    
    def test_exceptions_import(self):
        """Test if exceptions module imports correctly."""
        from utils.exceptions import ValidationError, DatabaseError, AuthenticationError
        assert ValidationError is not None
        assert DatabaseError is not None
        assert AuthenticationError is not None
    
    def test_exception_creation(self):
        """Test custom exception creation."""
        from utils.exceptions import ValidationError, DatabaseError
        
        validation_error = ValidationError("Test validation error")
        assert str(validation_error) == "Test validation error"
        
        db_error = DatabaseError("Test database error")
        assert str(db_error) == "Test database error"


class TestLoggingModule:
    """Test logging module functionality."""
    
    def test_logging_import(self):
        """Test if logging module imports correctly."""
        from utils.logging import logger
        assert logger is not None
    
    def test_logger_properties(self):
        """Test logger properties."""
        from utils.logging import logger
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')


class TestUtilsModule:
    """Test utils helper module."""
    
    def test_helpers_import(self):
        """Test if helpers module imports correctly."""
        from utils.helpers import generate_uuid, load_json_file, clean_response_sources
        assert callable(generate_uuid)
        assert callable(load_json_file)
        assert callable(clean_response_sources)


class TestIntegration:
    """Integration tests for the refactored modules (excluding AI service)."""
    
    def test_core_modules_work_together(self):
        """Test that core modules can be imported and used together."""
        from config import Config
        from database import DatabaseManager
        from auth import AuthService
        from utils.validation import validate_token_format
        from utils.logging import logger
        
        # Create instances
        config = Config()
        db_manager = DatabaseManager(':memory:')
        auth_service = AuthService()
        
        # Test operations
        is_valid_token = validate_token_format("12345678-1234-4567-8901-123456789012")
        
        assert config is not None
        assert db_manager is not None
        assert auth_service is not None
        assert logger is not None
        assert is_valid_token is True
