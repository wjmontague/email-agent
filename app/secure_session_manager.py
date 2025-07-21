#!/usr/bin/env python3
"""
Secure Session Manager
Auto-generated session security module
"""

import secrets
import time
import json
from typing import Dict, Optional

class SecureSessionManager:
    """Secure session management"""
    
    def __init__(self):
        self.sessions = {}
        self.SESSION_TIMEOUT = 8 * 3600  # 8 hours
        self.CSRF_TOKEN_LENGTH = 32
    
    def create_session(self, user_id: str, ip_address: str = None) -> Dict:
        """Create a new secure session"""
        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_hex(self.CSRF_TOKEN_LENGTH)
        
        session_data = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'ip_address': ip_address,
            'csrf_token': csrf_token
        }
        
        self.sessions[session_token] = session_data
        
        return {
            'session_token': session_token,
            'csrf_token': csrf_token,
            'expires_in': self.SESSION_TIMEOUT
        }
    
    def validate_session(self, session_token: str, csrf_token: str = None) -> Dict:
        """Validate session and optionally CSRF token"""
        if not session_token or session_token not in self.sessions:
            return {'valid': False, 'error': 'invalid_session'}
        
        session_data = self.sessions[session_token]
        current_time = time.time()
        
        # Check timeout
        if current_time - session_data['last_activity'] > self.SESSION_TIMEOUT:
            del self.sessions[session_token]
            return {'valid': False, 'error': 'session_expired'}
        
        # Validate CSRF if provided
        if csrf_token and not secrets.compare_digest(csrf_token, session_data['csrf_token']):
            return {'valid': False, 'error': 'csrf_mismatch'}
        
        # Update activity
        session_data['last_activity'] = current_time
        
        return {
            'valid': True,
            'user_id': session_data['user_id'],
            'csrf_token': session_data['csrf_token']
        }
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke a session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        sessions_to_remove = []
        for token, data in self.sessions.items():
            if data['user_id'] == user_id:
                sessions_to_remove.append(token)
        
        for token in sessions_to_remove:
            del self.sessions[token]
        
        return len(sessions_to_remove)
