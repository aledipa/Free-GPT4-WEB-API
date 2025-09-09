"""Database models and operations for FreeGPT4 Web API."""

import sqlite3
import json
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from uuid import uuid4

from werkzeug.security import generate_password_hash, check_password_hash

from config import config
from utils.exceptions import DatabaseError, ValidationError
from utils.logging import logger
from utils.validation import validate_username, validate_password
from utils.helpers import generate_uuid

@dataclass
class UserSettings:
    """User settings data model."""
    token: str
    provider: str = config.api.default_provider
    model: str = config.api.default_model
    system_prompt: str = ""
    message_history: bool = False
    username: str = ""
    password: str = ""
    chat_history: str = ""

@dataclass
class ServerSettings:
    """Server settings data model."""
    id: int = 1
    keyword: str = config.api.default_keyword
    file_input: bool = True
    port: str = str(config.server.port)
    provider: str = config.api.default_provider
    model: str = config.api.default_model
    cookie_file: str = config.files.cookies_file
    token: str = ""
    remove_sources: bool = True
    system_prompt: str = ""
    message_history: bool = False
    proxies: bool = False
    password: str = ""
    fast_api: bool = False
    virtual_users: bool = False
    chat_history: str = ""

class DatabaseManager:
    """Database manager for FreeGPT4 Web API."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path or config.database.settings_file
        self._ensure_db_directory()
        self.initialize_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager.
        
        Yields:
            Database connection and cursor
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            yield conn, cursor
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self):
        """Initialize database tables."""
        try:
            with self.get_connection() as (conn, cursor):
                # Create settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY,
                        keyword TEXT NOT NULL,
                        file_input BOOLEAN NOT NULL,
                        port TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        model TEXT NOT NULL,
                        cookie_file TEXT NOT NULL,
                        token TEXT NOT NULL,
                        remove_sources BOOLEAN NOT NULL,
                        system_prompt TEXT NOT NULL,
                        message_history BOOLEAN NOT NULL,
                        proxies BOOLEAN NOT NULL,
                        password TEXT NOT NULL,
                        fast_api BOOLEAN NOT NULL,
                        virtual_users BOOLEAN NOT NULL,
                        chat_history TEXT NOT NULL
                    )
                """)
                
                # Create personal settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS personal (
                        token TEXT PRIMARY KEY,
                        provider TEXT NOT NULL,
                        model TEXT NOT NULL,
                        system_prompt TEXT NOT NULL,
                        message_history BOOLEAN NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        chat_history TEXT NOT NULL
                    )
                """)
                
                # Insert default settings if not exists
                cursor.execute("SELECT COUNT(*) FROM settings")
                if cursor.fetchone()[0] == 0:
                    self._create_default_settings(cursor)
                
                conn.commit()
                logger.info("Database initialized successfully")
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    def _create_default_settings(self, cursor):
        """Create default settings."""
        default_settings = ServerSettings()
        cursor.execute("""
            INSERT INTO settings (
                id, keyword, file_input, port, provider, model, cookie_file,
                token, remove_sources, system_prompt, message_history, proxies,
                password, fast_api, virtual_users, chat_history
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            default_settings.id,
            default_settings.keyword,
            default_settings.file_input,
            default_settings.port,
            default_settings.provider,
            default_settings.model,
            default_settings.cookie_file,
            default_settings.token,
            default_settings.remove_sources,
            default_settings.system_prompt,
            default_settings.message_history,
            default_settings.proxies,
            default_settings.password,
            default_settings.fast_api,
            default_settings.virtual_users,
            default_settings.chat_history
        ))
        logger.info("Default settings created")
    
    def get_settings(self) -> Dict[str, Any]:
        """Get server settings.
        
        Returns:
            Dictionary with server settings
        """
        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("SELECT * FROM settings WHERE id = 1")
                row = cursor.fetchone()
                
                if not row:
                    raise DatabaseError("Settings not found")
                
                return {
                    "keyword": row["keyword"],
                    "file_input": bool(row["file_input"]),
                    "port": row["port"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "cookie_file": row["cookie_file"],
                    "token": row["token"],
                    "remove_sources": bool(row["remove_sources"]),
                    "system_prompt": row["system_prompt"],
                    "message_history": bool(row["message_history"]),
                    "proxies": bool(row["proxies"]),
                    "password": row["password"],
                    "fast_api": bool(row["fast_api"]),
                    "virtual_users": bool(row["virtual_users"])
                }
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to get settings: {e}")
            raise DatabaseError(f"Failed to get settings: {e}")
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update server settings.
        
        Args:
            settings: Dictionary with settings to update
        """
        try:
            with self.get_connection() as (conn, cursor):
                # Build dynamic update query
                update_fields = []
                values = []
                
                for key, value in settings.items():
                    if key == "password" and value:
                        # Hash password before storing
                        value = generate_password_hash(value)
                    update_fields.append(f"{key} = ?")
                    values.append(value)
                
                if update_fields:
                    query = f"UPDATE settings SET {', '.join(update_fields)} WHERE id = 1"
                    cursor.execute(query, values)
                    conn.commit()
                    logger.info("Settings updated successfully")
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            raise DatabaseError(f"Failed to update settings: {e}")
    
    def verify_admin_password(self, password: str) -> bool:
        """Verify admin password.
        
        Args:
            password: Password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            settings = self.get_settings()
            stored_password = settings.get("password", "")
            
            # If no password is set, deny access (more secure default)
            if not stored_password:
                logger.warning("Admin login attempted but no password is configured")
                return False
            
            # Verify password hash
            is_valid = check_password_hash(stored_password, password)
            
            if is_valid:
                logger.info("Admin authentication successful")
            else:
                logger.warning(f"Admin authentication failed for password attempt")
            
            return is_valid
        except Exception as e:
            logger.error(f"Failed to verify admin password: {e}")
            return False
    
    def create_user(self, username: str, password: Optional[str] = None) -> str:
        """Create a new user.
        
        Args:
            username: Username
            password: Password (will be auto-generated if not provided)
            
        Returns:
            User token
            
        Raises:
            ValidationError: If username is invalid
            DatabaseError: If database operation fails
        """
        # Validate username
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            raise ValidationError(error_msg)
        
        # Validate password
        if password is None:
            password = username  # Default password
        
        is_valid, error_msg = validate_password(password, config.security.password_min_length)
        if not is_valid:
            raise ValidationError(error_msg)
        
        token = generate_uuid()
        hashed_password = generate_password_hash(password)
        
        user_settings = UserSettings(
            token=token,
            username=username,
            password=hashed_password
        )
        
        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("""
                    INSERT INTO personal (
                        token, provider, model, system_prompt, message_history,
                        username, password, chat_history
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_settings.token,
                    user_settings.provider,
                    user_settings.model,
                    user_settings.system_prompt,
                    user_settings.message_history,
                    user_settings.username,
                    user_settings.password,
                    user_settings.chat_history
                ))
                conn.commit()
                logger.info(f"User '{username}' created successfully")
                return token
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise ValidationError(f"Username '{username}' already exists")
            raise DatabaseError(f"Failed to create user: {e}")
        except Exception as e:
            logger.error(f"Failed to create user '{username}': {e}")
            raise DatabaseError(f"Failed to create user: {e}")
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user by token.
        
        Args:
            token: User token
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("SELECT * FROM personal WHERE token = ?", (token,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return {
                    "token": row["token"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "system_prompt": row["system_prompt"],
                    "message_history": bool(row["message_history"]),
                    "username": row["username"],
                    "password": row["password"],
                    "chat_history": row["chat_history"]
                }
        except Exception as e:
            logger.error(f"Failed to get user by token: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("SELECT * FROM personal WHERE username = ?", (username,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return {
                    "token": row["token"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "system_prompt": row["system_prompt"],
                    "message_history": bool(row["message_history"]),
                    "username": row["username"],
                    "password": row["password"],
                    "chat_history": row["chat_history"]
                }
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            return None
    
    def verify_user_password(self, username: str, password: str) -> bool:
        """Verify user password.
        
        Args:
            username: Username
            password: Password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            user = self.get_user_by_username(username)
            if not user:
                return False
            
            return check_password_hash(user["password"], password)
        except Exception as e:
            logger.error(f"Failed to verify user password: {e}")
            return False
    
    def update_user_settings(self, username: str, settings: Dict[str, Any]):
        """Update user settings.
        
        Args:
            username: Username
            settings: Settings to update
        """
        try:
            with self.get_connection() as (conn, cursor):
                # Build dynamic update query
                update_fields = []
                values = []
                
                for key, value in settings.items():
                    if key == "password" and value:
                        # Hash password before storing
                        value = generate_password_hash(value)
                    update_fields.append(f"{key} = ?")
                    values.append(value)
                
                if update_fields:
                    values.append(username)  # Add username for WHERE clause
                    query = f"UPDATE personal SET {', '.join(update_fields)} WHERE username = ?"
                    cursor.execute(query, values)
                    conn.commit()
                    logger.info(f"User '{username}' settings updated successfully")
        except Exception as e:
            logger.error(f"Failed to update user settings: {e}")
            raise DatabaseError(f"Failed to update user settings: {e}")
    
    def delete_user(self, username: str):
        """Delete user.
        
        Args:
            username: Username to delete
        """
        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("DELETE FROM personal WHERE username = ?", (username,))
                conn.commit()
                logger.info(f"User '{username}' deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete user '{username}': {e}")
            raise DatabaseError(f"Failed to delete user: {e}")
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users.
        
        Returns:
            List of user dictionaries
        """
        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("SELECT * FROM personal")
                rows = cursor.fetchall()
                
                users = []
                for row in rows:
                    users.append({
                        "token": row["token"],
                        "provider": row["provider"],
                        "model": row["model"],
                        "system_prompt": row["system_prompt"],
                        "message_history": bool(row["message_history"]),
                        "username": row["username"],
                        "password": row["password"],
                        "chat_history": row["chat_history"]
                    })
                
                return users
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            raise DatabaseError(f"Failed to get all users: {e}")
    
    def save_chat_history(self, username: str, chat_history: str):
        """Save chat history for user or admin.
        
        Args:
            username: Username ('admin' for admin user)
            chat_history: Chat history JSON string
        """
        try:
            with self.get_connection() as (conn, cursor):
                if username == "admin":
                    cursor.execute("UPDATE settings SET chat_history = ? WHERE id = 1", (chat_history,))
                else:
                    cursor.execute("UPDATE personal SET chat_history = ? WHERE username = ?", (chat_history, username))
                
                conn.commit()
                logger.debug(f"Chat history saved for user '{username}'")
        except Exception as e:
            logger.error(f"Failed to save chat history for user '{username}': {e}")
            raise DatabaseError(f"Failed to save chat history: {e}")
    
    def get_chat_history(self, username: str) -> str:
        """Get chat history for user or admin.
        
        Args:
            username: Username ('admin' for admin user)
            
        Returns:
            Chat history JSON string
        """
        try:
            with self.get_connection() as (conn, cursor):
                if username == "admin":
                    cursor.execute("SELECT chat_history FROM settings WHERE id = 1")
                else:
                    cursor.execute("SELECT chat_history FROM personal WHERE username = ?", (username,))
                
                row = cursor.fetchone()
                return row["chat_history"] if row else ""
        except Exception as e:
            logger.error(f"Failed to get chat history for user '{username}': {e}")
            return ""

# Global database manager instance
db_manager = DatabaseManager()
