#!/usr/bin/env python3
"""
Authentication Security Configuration
Auto-generated secure authentication settings
"""

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

# CSRF Protection
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

# Rate Limiting
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Password Requirements
MIN_PASSWORD_LENGTH = 12
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_NUMBERS = True
REQUIRE_SPECIAL_CHARS = True

# Security Headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
}
