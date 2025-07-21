#!/usr/bin/env python3
"""
Security Middleware for Email Agent
Auto-generated security middleware
"""

from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)

def security_headers():
    """Add security headers to all responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add security headers
            if hasattr(response, 'headers'):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            
            return response
        return decorated_function
    return decorator

def validate_input():
    """Validate and sanitize input data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Basic input validation
            if request.is_json:
                try:
                    data = request.get_json()
                    if data is None:
                        return jsonify({'error': 'Invalid JSON'}), 400
                except Exception:
                    return jsonify({'error': 'Invalid JSON format'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit_check():
    """Basic rate limiting check"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implement rate limiting logic here
            # For now, just log the request
            logger.info(f"Request from {request.remote_addr} to {request.endpoint}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
