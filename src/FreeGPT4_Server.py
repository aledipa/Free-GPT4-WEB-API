"""FreeGPT4 Web API - A Web API for GPT-4.

Repo: github.com/aledipa/FreeGPT4-WEB-API
By: Alessandro Di Pasquale
GPT4Free Credits: github.com/xtekky/gpt4free
"""

import os
import argparse
import threading
import getpass
import json
from pathlib import Path
from typing import Optional

from flask import Flask, request, render_template, redirect, jsonify, session
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from g4f.api import run_api

from config import config
from database import db_manager
from auth import auth_service, require_auth, require_token_auth
from ai_service import ai_service
from utils.logging import logger, setup_logging
from utils.exceptions import (
    FreeGPTException, 
    ValidationError, 
    AuthenticationError,
    AIProviderError,
    FileUploadError
)
from utils.validation import (
    validate_file_upload,
    validate_port,
    validate_proxy_format,
    sanitize_input
)
from utils.helpers import (
    generate_uuid,
    load_json_file,
    save_json_file,
    parse_proxy_url,
    safe_filename
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.security.secret_key
app.config['UPLOAD_FOLDER'] = config.files.upload_folder
app.config['MAX_CONTENT_LENGTH'] = config.server.max_content_length

# Set up logging
if os.getenv('LOG_LEVEL'):
    setup_logging(level=os.getenv('LOG_LEVEL'))

logger.info("FreeGPT4 Web API - Starting server...")
logger.info("Repo: github.com/aledipa/FreeGPT4-WEB-API")
logger.info("By: Alessandro Di Pasquale")
logger.info("GPT4Free Credits: github.com/xtekky/gpt4free")

class ServerArgumentParser:
    """Parse and manage server arguments."""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.args = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(description="FreeGPT4 Web API Server")
        
        parser.add_argument(
            "--remove-sources",
            action='store_true',
            help="Remove the sources from the response",
        )
        parser.add_argument(
            "--enable-gui",
            action='store_true',
            help="Use a graphical interface for settings",
        )
        parser.add_argument(
            "--private-mode",
            action='store_true',
            help="Use a private token to access the API",
        )
        parser.add_argument(
            "--enable-proxies",
            action='store_true',
            help="Use one or more proxies to avoid being blocked or banned",
        )
        parser.add_argument(
            "--enable-history",
            action='store_true',
            help="Enable the history of the messages",
        )
        parser.add_argument(
            "--password",
            action='store',
            help="Set or change the password for the settings page [mandatory in docker environment]",
        )
        parser.add_argument(
            "--cookie-file",
            action='store',
            type=str,
            help="Use a cookie file",
        )
        parser.add_argument(
            "--file-input",
            action='store_true',
            help="Add the file as input support",
        )
        parser.add_argument(
            "--port",
            action='store',
            type=int,
            help="Change the port (default: 5500)",
        )
        parser.add_argument(
            "--model",
            action='store',
            type=str,
            help="Change the model (default: gpt-4)",
        )
        parser.add_argument(
            "--provider",
            action='store',
            type=str,
            help="Change the provider (default: Auto)",
        )
        parser.add_argument(
            "--keyword",
            action='store',
            type=str,
            help="Add the keyword support",
        )
        parser.add_argument(
            "--system-prompt",
            action='store',
            type=str,
            help="Use a system prompt to 'customize' the answers",
        )
        parser.add_argument(
            "--enable-fast-api",
            action='store_true',
            help="Use the fast API standard (PORT 1336 - compatible with OpenAI integrations)",
        )
        parser.add_argument(
            "--enable-virtual-users",
            action='store_true',
            help="Gives the chance to create and manage new users",
        )
        
        return parser
    
    def parse_args(self):
        """Parse command line arguments."""
        self.args, _ = self.parser.parse_known_args()
        return self.args

class ServerManager:
    """Manage server configuration and state."""
    
    def __init__(self, args):
        self.args = args
        self.fast_api_thread = None
        self._setup_working_directory()
        self._merge_settings_with_args()
    
    def _setup_working_directory(self):
        """Set up working directory."""
        script_path = Path(__file__).resolve()
        os.chdir(script_path.parent)
    
    def _merge_settings_with_args(self):
        """Merge database settings with command line arguments."""
        try:
            settings = db_manager.get_settings()
            
            # Update args with database settings if not specified
            if not self.args.keyword:
                self.args.keyword = settings.get("keyword", config.api.default_keyword)
            
            if not self.args.file_input:
                self.args.file_input = settings.get("file_input", True)
            
            if not self.args.port:
                self.args.port = int(settings.get("port", config.server.port))
            
            if not self.args.provider:
                self.args.provider = settings.get("provider", config.api.default_provider)
            
            if not self.args.model:
                self.args.model = settings.get("model", config.api.default_model)
            
            if not self.args.cookie_file:
                self.args.cookie_file = settings.get("cookie_file", config.files.cookies_file)
            
            if not self.args.remove_sources:
                self.args.remove_sources = settings.get("remove_sources", True)
            
            if not self.args.system_prompt:
                self.args.system_prompt = settings.get("system_prompt", "")
            
            if not self.args.enable_history:
                self.args.enable_history = settings.get("message_history", False)
            
            if not self.args.enable_proxies:
                self.args.enable_proxies = settings.get("proxies", False)
            
            # Handle private mode token
            token = settings.get("token", "")
            if self.args.private_mode and not token:
                token = generate_uuid()
                db_manager.update_settings({"token": token})
            elif token:
                self.args.private_mode = True
            
            self.args.token = token
            
            # Handle fast API
            if self.args.enable_fast_api or settings.get("fast_api", False):
                self.start_fast_api()
            
            # Handle virtual users
            if not hasattr(self.args, 'enable_virtual_users'):
                self.args.enable_virtual_users = settings.get("virtual_users", False)
            
        except Exception as e:
            logger.error(f"Failed to merge settings: {e}")
            # Use defaults
            self.args.keyword = self.args.keyword or config.api.default_keyword
            self.args.port = self.args.port or config.server.port
            self.args.provider = self.args.provider or config.api.default_provider
            self.args.model = self.args.model or config.api.default_model
    
    def start_fast_api(self):
        """Start Fast API in background thread."""
        if self.fast_api_thread and self.fast_api_thread.is_alive():
            return
        
        logger.info(f"Starting Fast API on port {config.api.fast_api_port}")
        self.fast_api_thread = threading.Thread(target=run_api, name="fastapi", daemon=True)
        self.fast_api_thread.start()
    
    def setup_password(self):
        """Set up admin password if GUI is enabled."""
        if not self.args.enable_gui:
            logger.info("GUI disabled - no password setup required")
            return
        
        try:
            settings = db_manager.get_settings()
            current_password = settings.get("password", "")
            
            if self.args.password:
                # Password provided via command line
                password = self.args.password
                confirm_password = password
                logger.info("Using password provided via command line argument")
            elif not current_password:
                # No password set, prompt for new one
                logger.info("No admin password configured. Setting up new password...")
                password = getpass.getpass("Settings page password:\n > ")
                confirm_password = getpass.getpass("Confirm password:\n > ")
            else:
                # Password already set
                logger.info("Admin password already configured")
                return
            
            # Validate passwords
            if not password or not confirm_password:
                logger.error("Password cannot be empty")
                exit(1)
            
            if password != confirm_password:
                logger.error("Passwords don't match")
                exit(1)
            
            # Additional password strength validation
            if len(password) < config.security.password_min_length:
                logger.error(f"Password must be at least {config.security.password_min_length} characters long")
                exit(1)
            
            # Save password (will be hashed automatically in update_settings)
            db_manager.update_settings({"password": password})
            logger.info("Admin password configured successfully")
            
            # Verify the password was saved correctly
            if not db_manager.verify_admin_password(password):
                logger.error("Password verification failed after setup")
                exit(1)
            
            logger.info("Password verification successful")
            
        except Exception as e:
            logger.error(f"Failed to setup password: {e}")
            exit(1)
# Routes and handlers
@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(FreeGPTException)
def handle_freegpt_exception(e):
    """Handle FreeGPT exceptions."""
    logger.error(f"FreeGPT error: {e}")
    return jsonify({"error": str(e)}), 400

@app.errorhandler(Exception)
def handle_general_exception(e):
    """Handle general exceptions."""
    from werkzeug.exceptions import NotFound
    
    # Don't log 404 errors as unexpected errors
    if isinstance(e, NotFound):
        return jsonify({"error": "Not found"}), 404
    
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

@app.route("/", methods=["GET", "POST"])
def index():
    """Main API endpoint for chat completion."""
    import asyncio
    
    async def _async_index():
        try:
            # Get current settings
            settings = db_manager.get_settings()
            
            # Extract question from request
            question = None
            if request.method == "GET":
                question = request.args.get(server_manager.args.keyword)
            else:
                # Handle file upload
                if 'file' in request.files:
                    file = request.files['file']
                    is_valid, error_msg = validate_file_upload(file, config.files.allowed_extensions)
                    if not is_valid:
                        raise FileUploadError(error_msg)
                    
                    question = file.read().decode('utf-8')
            
            if not question:
                return "<p id='response'>Please enter a question</p>"
            
            # Sanitize input
            question = sanitize_input(question, 10000)  # 10KB limit
            
            # Verify token access
            token = request.args.get("token")
            username = auth_service.verify_token_access(
                token, 
                server_manager.args.private_mode
            )
            
            if server_manager.args.private_mode and not username:
                return "<p id='response'>Invalid token</p>"
            
            if not username:
                username = "admin"
            
            # Generate AI response
            response_text = await ai_service.generate_response(
                message=question,
                username=username,
                use_history=server_manager.args.enable_history,
                remove_sources=server_manager.args.remove_sources,
                use_proxies=server_manager.args.enable_proxies,
                cookie_file=server_manager.args.cookie_file
            )
            
            logger.info(f"Generated response for user '{username}' ({len(response_text)} chars)")
            return response_text
            
        except FreeGPTException as e:
            logger.error(f"API error: {e}")
            return f"<p id='response'>Error: {e}</p>"
        except Exception as e:
            logger.error(f"Unexpected API error: {e}", exc_info=True)
            return "<p id='response'>Internal server error</p>"
    
    # Run the async function
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_async_index())
    except Exception as e:
        logger.error(f"Async execution error: {e}", exc_info=True)
        return f"<p id='response'>Error: AI API call failed: {e}</p>"
    finally:
        loop.close()

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if not server_manager.args.enable_gui:
        return "The GUI is disabled. Use the --enable-gui argument to enable it."
    
    return render_template(
        "login.html",
        virtual_users=server_manager.args.enable_virtual_users
    )

@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Settings page."""
    if request.method == "GET":
        return redirect("/login", code=302)
    
    try:
        # Authenticate user
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
        is_admin = False
        if username == "admin":
            is_admin = auth_service.authenticate_admin(username, password)
            if not is_admin:
                return render_template(
                    "login.html",
                    virtual_users=server_manager.args.enable_virtual_users,
                    error="Invalid admin credentials"
                )
        else:
            is_admin = False
            if not auth_service.authenticate_user(username, password):
                return render_template(
                    "login.html",
                    virtual_users=server_manager.args.enable_virtual_users,
                    error="Invalid credentials"
                )
        
        if not is_admin and username != "admin":
            # Regular user settings
            user_data = db_manager.get_user_by_username(username)
            if not user_data:
                return render_template(
                    "login.html",
                    virtual_users=server_manager.args.enable_virtual_users,
                    error="User not found"
                )
        
        # Prepare template data
        template_data = {
            "username": username,
            "virtual_users": server_manager.args.enable_virtual_users,
            "providers": config.available_providers,
            "generic_models": config.generic_models
        }
        
        if is_admin:
            # Admin settings (only if properly authenticated)
            template_data["data"] = db_manager.get_settings()
            
            # Load proxies
            proxies_path = Path(config.files.proxies_file)
            template_data["proxies"] = load_json_file(proxies_path, [])
            
            # Load users for virtual users feature
            if server_manager.args.enable_virtual_users:
                template_data["users_data"] = db_manager.get_all_users()
        else:
            # User settings
            template_data["data"] = user_data
        
        return render_template("settings.html", **template_data)
        
    except Exception as e:
        logger.error(f"Settings page error: {e}")
        return render_template(
            "login.html",
            virtual_users=server_manager.args.enable_virtual_users,
            error="An error occurred"
        )

@app.route("/save", methods=["POST"])
def save_settings():
    """Save admin settings."""
    try:
        # Authenticate admin
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
        if not auth_service.authenticate_admin(username, password):
            return render_template(
                "login.html",
                virtual_users=server_manager.args.enable_virtual_users,
                error="Invalid admin credentials"
            )
        
        # Process settings update
        settings_update = {}
        
        # Boolean settings
        bool_fields = [
            "file_input", "remove_sources", "message_history", 
            "proxies", "fast_api", "virtual_users"
        ]
        for field in bool_fields:
            settings_update[field] = request.form.get(field) == "true"
        
        # String settings
        string_fields = ["port", "model", "keyword", "provider", "system_prompt"]
        for field in string_fields:
            value = request.form.get(field, "")
            if field == "port":
                is_valid, error_msg = validate_port(value)
                if not is_valid:
                    raise ValidationError(f"Invalid port: {error_msg}")
            settings_update[field] = sanitize_input(value)
        
        # Handle password update
        new_password = request.form.get("new_password", "")
        if new_password:
            confirm_password = request.form.get("confirm_password", "")
            if new_password != confirm_password:
                raise ValidationError("Passwords do not match")
            settings_update["password"] = new_password
        
        # Handle private mode token
        if request.form.get("private_mode") == "true":
            token = request.form.get("token", "")
            if not token:
                token = generate_uuid()
            settings_update["token"] = token
        else:
            settings_update["token"] = ""
        
        # Handle file upload
        if 'cookie_file' in request.files:
            file = request.files['cookie_file']
            if file.filename:
                is_valid, error_msg = validate_file_upload(file, config.files.allowed_extensions)
                if not is_valid:
                    raise FileUploadError(error_msg)
                
                filename = safe_filename(file.filename)
                file_path = Path(app.config['UPLOAD_FOLDER']) / filename
                file.save(str(file_path))
                settings_update["cookie_file"] = str(file_path)
        
        # Handle proxies
        if request.form.get("proxies") == "true":
            proxies = []
            i = 1
            while f"proxy_{i}" in request.form:
                proxy_url = request.form.get(f"proxy_{i}", "").strip()
                if proxy_url:
                    if not validate_proxy_format(proxy_url):
                        raise ValidationError(f"Invalid proxy format: {proxy_url}")
                    
                    proxy_dict = parse_proxy_url(proxy_url)
                    if proxy_dict:
                        proxies.append(proxy_dict)
                i += 1
            
            # Save proxies to file
            proxies_path = Path(config.files.proxies_file)
            save_json_file(proxies_path, proxies)
        
        # Handle virtual users
        if request.form.get("virtual_users") == "true":
            current_users = {user["token"]: user["username"] for user in db_manager.get_all_users()}
            form_users = {}
            
            # Extract user data from form
            for key, value in request.form.items():
                if key.startswith("username_"):
                    token = key.split("_", 1)[1]
                    form_users[token] = sanitize_input(value, 50)
            
            # Add new users
            for token, username in form_users.items():
                if token not in current_users and username:
                    try:
                        db_manager.create_user(username)
                    except ValidationError as e:
                        logger.warning(f"Could not create user '{username}': {e}")
            
            # Update existing users
            for token, username in form_users.items():
                if token in current_users and username != current_users[token]:
                    try:
                        user = db_manager.get_user_by_token(token)
                        if user:
                            db_manager.update_user_settings(user["username"], {"username": username})
                    except Exception as e:
                        logger.warning(f"Could not update user: {e}")
            
            # Remove deleted users
            for token in current_users:
                if token not in form_users:
                    try:
                        user = db_manager.get_user_by_token(token)
                        if user:
                            db_manager.delete_user(user["username"])
                    except Exception as e:
                        logger.warning(f"Could not delete user: {e}")
        
        # Save settings
        db_manager.update_settings(settings_update)
        
        # Restart Fast API if needed
        if settings_update.get("fast_api") and not server_manager.fast_api_thread:
            server_manager.start_fast_api()
        
        logger.info("Settings saved successfully")
        return "Settings saved and applied successfully!"
        
    except FreeGPTException as e:
        logger.error(f"Settings save error: {e}")
        return f"Error: {e}"
    except Exception as e:
        logger.error(f"Unexpected settings save error: {e}")
        return "Error: Failed to save settings"

@app.route("/save/<username>", methods=["POST"])
def save_user_settings(username):
    """Save user-specific settings."""
    try:
        # Authenticate user
        password = request.form.get("password", "")
        
        if not auth_service.authenticate_user(username, password):
            return render_template(
                "login.html",
                virtual_users=server_manager.args.enable_virtual_users,
                error="Invalid credentials"
            )
        
        # Process user settings update
        settings_update = {}
        
        # String settings
        string_fields = ["provider", "model", "system_prompt"]
        for field in string_fields:
            value = request.form.get(field, "")
            settings_update[field] = sanitize_input(value)
        
        # Boolean settings
        settings_update["message_history"] = request.form.get("message_history") == "true"
        
        # Handle password update
        new_password = request.form.get("new_password", "")
        if new_password:
            confirm_password = request.form.get("confirm_password", "")
            if new_password != confirm_password:
                raise ValidationError("Passwords do not match")
            settings_update["password"] = new_password
        
        # Save user settings
        db_manager.update_user_settings(username, settings_update)
        
        logger.info(f"User settings saved for '{username}'")
        return "Settings saved successfully!"
        
    except FreeGPTException as e:
        logger.error(f"User settings save error: {e}")
        return f"Error: {e}"
    except Exception as e:
        logger.error(f"Unexpected user settings save error: {e}")
        return "Error: Failed to save settings"

@app.route("/models", methods=["GET"])
def get_models():
    """Get available models for a provider."""
    provider = request.args.get("provider", "Auto")
    return jsonify(ai_service.get_available_models(provider))

@app.route("/generatetoken", methods=["GET", "POST"])
def generate_token():
    """Generate a new token."""
    return generate_uuid()

@app.route("/favicon.ico")
def favicon():
    """Serve favicon."""
    try:
        from flask import send_from_directory
        return send_from_directory(
            str(Path(app.static_folder) / "img"), 
            "favicon(Nicoladipa).png",
            mimetype='image/png'
        )
    except:
        # Return empty response if favicon not found
        return "", 204

def main():
    """Main entry point."""
    try:
        # Parse arguments
        arg_parser = ServerArgumentParser()
        args = arg_parser.parse_args()
        
        # Initialize server manager
        global server_manager
        server_manager = ServerManager(args)
        
        # Set up password if needed
        server_manager.setup_password()
        
        logger.info(f"Server configuration:")
        logger.info(f"  Port: {args.port}")
        logger.info(f"  Provider: {args.provider}")
        logger.info(f"  Model: {args.model}")
        logger.info(f"  Private mode: {args.private_mode}")
        logger.info(f"  GUI enabled: {args.enable_gui}")
        logger.info(f"  History enabled: {args.enable_history}")
        logger.info(f"  Proxies enabled: {args.enable_proxies}")
        logger.info(f"  Virtual users: {args.enable_virtual_users}")
        
        # Start server
        app.run(
            host=config.server.host,
            port=args.port,
            debug=config.server.debug
        )
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()