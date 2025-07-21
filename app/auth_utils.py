#!/usr/bin/env python3
"""
Authentication Utilities
Simple functions for checking login status
"""

from flask import session

def is_logged_in():
    """Check if user is currently logged in"""
    return session.get('logged_in', False)

def get_current_user():
    """Get current user info from session"""
    if is_logged_in():
        return {
            'username': session.get('username', 'Unknown'),
            'logged_in': True
        }
    return {'logged_in': False}

def require_login():
    """Simple function to check login requirement"""
    return is_logged_in()
