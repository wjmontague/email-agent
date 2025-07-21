#!/usr/bin/env python3
"""
Secure Authentication Decorator (Updated for existing system)
Compatible with existing Flask session management
"""

from functools import wraps
from flask import request, jsonify, session, redirect, url_for
import logging

logger = logging.getLogger(__name__)

def require_auth(require_csrf=False):
    """Decorator to require authentication for routes (compatible with existing system)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in using existing session system
            if 'logged_in' not in session or not session['logged_in']:
                # For API endpoints, return JSON error
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # For web pages, redirect to login
                return redirect(url_for('auth.login'))
            
            # If CSRF is required (for state-changing operations)
            if require_csrf and request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                # For now, just log CSRF requirement - can be enhanced later
                logger.info(f"CSRF check required for {request.path}")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def add_security_headers():
    """Decorator to add security headers to responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add security headers if response has headers attribute
            if hasattr(response, 'headers'):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                # Note: Commented out HSTS for development/HTTP
                # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
        
        return decorated_function
    return decorator

def login_required(f):
    """Simple login required decorator (alternative to require_auth)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Login required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
