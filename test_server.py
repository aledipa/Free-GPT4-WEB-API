#!/usr/bin/env python3
"""Test server to verify the refactored codebase works without g4f dependencies."""

import sys
import os
sys.path.insert(0, 'src')

from flask import Flask, jsonify, request
from config import config
from database import db_manager  
from auth import auth_service
from utils.logging import logger
from utils.validation import validate_proxy_format, validate_token_format

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.security.secret_key

@app.route('/')
def index():
    """Home page."""
    return jsonify({
        'status': 'success',
        'message': 'FreeGPT4 Web API - Refactored Version',
        'version': '2.0.0',
        'modules_loaded': True,
        'database_connected': db_manager is not None,
        'auth_service_ready': auth_service is not None
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM settings")
            settings_count = cursor.fetchone()[0]
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'settings_count': settings_count,
            'auth_service': 'ready',
            'timestamp': logger.name  # Just to test logger
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate_data():
    """Test validation endpoints."""
    data = request.get_json() or {}
    
    results = {}
    
    if 'proxy' in data:
        results['proxy_valid'] = validate_proxy_format(data['proxy'])
    
    if 'token' in data:
        results['token_valid'] = validate_token_format(data['token'])
    
    return jsonify({
        'status': 'success',
        'validation_results': results
    })

@app.route('/api/config')
def get_config():
    """Get configuration info."""
    return jsonify({
        'server': {
            'host': config.server.host,
            'port': config.server.port,
            'debug': config.server.debug
        },
        'database': {
            'type': 'SQLite',
            'file': config.database.settings_file
        },
        'security': {
            'secret_key_set': bool(config.security.secret_key)
        }
    })

if __name__ == '__main__':
    logger.info("Starting test server...")
    print("🚀 Starting FreeGPT4 Test Server...")
    print(f"📊 Database: {config.database.settings_file}")
    print(f"🔐 Auth service initialized: {auth_service is not None}")
    print(f"🌐 Server will run on {config.server.host}:{config.server.port}")
    
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug
    )
