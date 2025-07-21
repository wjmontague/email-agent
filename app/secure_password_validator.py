#!/usr/bin/env python3
"""
Secure Password Validator
Auto-generated password security module
"""

import re
import hashlib
import secrets
from typing import Tuple

class PasswordValidator:
    """Secure password validation"""
    
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    @staticmethod
    def validate_strength(password: str) -> Tuple[bool, str]:
        """Validate password meets security requirements"""
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long"
        
        if PasswordValidator.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if PasswordValidator.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if PasswordValidator.REQUIRE_NUMBERS and not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if PasswordValidator.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check for weak patterns
        weak_patterns = [
            r'(.)\1{2,}',  # Repeated characters
            r'123456',      # Sequential numbers
            r'abcdef',      # Sequential letters
            r'password',    # Common words
            r'qwerty'
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                return False, "Password contains weak patterns"
        
        return True, "Password is strong"

class SecurePasswordManager:
    """Secure password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with secure salt"""
        salt = secrets.token_hex(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)  # 100,000 iterations
        return f"{salt}${pwdhash.hex()}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, pwdhash = stored_hash.split('$')
            test_hash = hashlib.pbkdf2_hmac('sha256',
                                           password.encode('utf-8'),
                                           salt.encode('utf-8'),
                                           100000)
            return secrets.compare_digest(pwdhash, test_hash.hex())
        except Exception:
            return False

class RateLimiter:
    """Rate limiting for authentication attempts"""
    
    def __init__(self):
        self._attempts = {}
        self.MAX_ATTEMPTS = 5
        self.LOCKOUT_MINUTES = 15
    
    def is_rate_limited(self, identifier: str) -> Tuple[bool, int]:
        """Check if identifier is rate limited"""
        import time
        current_time = time.time()
        
        if identifier in self._attempts:
            attempts = self._attempts[identifier]
            # Remove old attempts
            cutoff = current_time - (self.LOCKOUT_MINUTES * 60)
            attempts = [t for t in attempts if t > cutoff]
            self._attempts[identifier] = attempts
            
            if len(attempts) >= self.MAX_ATTEMPTS:
                remaining = int((attempts[0] + (self.LOCKOUT_MINUTES * 60)) - current_time)
                return True, max(0, remaining)
        
        return False, 0
    
    def record_attempt(self, identifier: str, success: bool):
        """Record authentication attempt"""
        import time
        if success:
            if identifier in self._attempts:
                del self._attempts[identifier]
        else:
            if identifier not in self._attempts:
                self._attempts[identifier] = []
            self._attempts[identifier].append(time.time())
